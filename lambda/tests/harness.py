"""Arnés compartido por las pruebas: arma la skill real con dobles de AWS y simula a Alexa.

La skill se construye con `build_skill()` (el mismo código que corre en Lambda); solo se
reemplazan los clientes boto3 por los dobles de `tests/fakes.py` y el reloj por uno simulado,
así las pruebas corren sin cuenta de AWS, sin red y sin esperas reales.
"""
import json
import pathlib
import re

from tests.fakes import FakeDynamoDB, FakeIot, FakeIotData
from vigilante.config import Settings
from vigilante.device_gateway import DeviceGateway
from vigilante.link_repository import LinkRepository
from vigilante.skill import build_skill

LAMBDA_DIR = pathlib.Path(__file__).resolve().parent.parent
REPO_ROOT = LAMBDA_DIR.parent
EVENTS = LAMBDA_DIR / "events"

THING_CODE = "123456"          # Thing del ESP32 (con certificado)
OTHER_CODE = "654321"          # Thing de prueba (sin certificado ni hardware)
THING = "vigilante-" + THING_CODE
OTHER = "vigilante-" + OTHER_CODE
USER = "amzn1.ask.account.USUARIO_DE_PRUEBA"
NOW = 1_800_000_000


class FakeClock:
    """Reloj monotónico simulado: `sleep` avanza el tiempo sin esperar."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


def _strip_ssml(ssml: str) -> str:
    return re.sub(r"<[^>]+>", "", ssml)


def build_event(request_type="IntentRequest", intent=None, user_id=USER, slots=None,
                confirmation="NONE"):
    """Arma un request de Alexa con la misma forma que el JSON Input del simulador."""
    application = {"applicationId": "amzn1.ask.skill.PRUEBA"}
    user = {"userId": user_id}
    request = {
        "type": request_type,
        "requestId": "amzn1.echo-api.request.prueba",
        "timestamp": "2026-11-08T10:00:00Z",
        "locale": "es-US",
    }
    if request_type == "IntentRequest":
        request["intent"] = {
            "name": intent,
            "confirmationStatus": confirmation,
            "slots": {
                name: {"name": name, "value": value, "confirmationStatus": "CONFIRMED"}
                for name, value in (slots or {}).items()
            },
        }
        request["dialogState"] = "COMPLETED"
    return {
        "version": "1.0",
        "session": {"new": request_type == "LaunchRequest",
                    "sessionId": "amzn1.echo-api.session.prueba",
                    "application": application, "user": user},
        "context": {"System": {"application": application, "user": user,
                               "apiEndpoint": "https://api.amazonalexa.com"}},
        "request": request,
    }


class Harness:
    """Skill + DynamoDB, registro de IoT y Shadow en memoria.

    `device_online=False` simula que ningún ESP32 está conectado; `offline_things`
    deja desconectados solo algunos Things (p. ej. el Thing de prueba sin hardware).
    """

    def __init__(self, device_online=True, offline_things=()):
        self.db = FakeDynamoDB()
        self.iot = FakeIot({THING, OTHER})
        self.data = FakeIotData(now=NOW, device_online=device_online,
                                offline_things=offline_things)
        self.clock = FakeClock()
        self.settings = Settings(iot_endpoint="example-ats.iot.us-east-2.amazonaws.com")
        gateway = DeviceGateway(self.iot, self.data, poll_interval_s=0.25,
                                clock=self.clock, sleep=self.clock.sleep)
        self.handler = build_skill(LinkRepository(self.db, self.settings.links_table), gateway,
                                   self.settings, now=lambda: NOW + 30).lambda_handler()
        self.last_response = None

    # --- Envío de eventos ---

    def send(self, event) -> str:
        """Invoca la skill y devuelve el texto hablado (sin etiquetas SSML)."""
        self.last_response = self.handler(event, None)
        return _strip_ssml(self.last_response["response"]["outputSpeech"]["ssml"])

    def say(self, event_file, **overrides) -> str:
        """Envía uno de los eventos de `lambda/events/` (los mismos de la consola de Lambda)."""
        event = json.loads((EVENTS / event_file).read_text(encoding="utf-8"))
        slots = event["request"].get("intent", {}).get("slots", {})
        if "codigo" in slots:
            # El código del archivo de eventos se edita para probar en la consola de Lambda
            # con el Thing real; las pruebas fijan siempre el suyo para no depender de él.
            slots["codigo"]["value"] = overrides.get("codigo", THING_CODE)
        if "confirmation" in overrides:
            event["request"]["intent"]["confirmationStatus"] = overrides["confirmation"]
        return self.send(event)

    def ask(self, intent, user_id=USER, codigo=None, confirmation="NONE") -> str:
        """Equivale a escribir una frase en el simulador que Alexa resuelve a `intent`."""
        slots = {"codigo": codigo} if codigo is not None else None
        return self.send(build_event(intent=intent, user_id=user_id, slots=slots,
                                     confirmation=confirmation))

    def launch(self, user_id=USER) -> str:
        """Equivale a "abre vigilante inteligente"."""
        return self.send(build_event("LaunchRequest", user_id=user_id))

    @property
    def session_ended(self) -> bool:
        return bool(self.last_response["response"].get("shouldEndSession"))

    # --- Estado observable (lo que se ve en DynamoDB y en la Sombra clásica) ---

    def linked_thing(self, user_id=USER):
        item = self.db.items.get(user_id)
        return item["thingName"]["S"] if item else None

    def shadow_state(self, thing=THING):
        return self.data.shadows.get(thing, {}).get("state", {})
