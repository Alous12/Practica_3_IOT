"""Pruebas de contrato entre las capas del proyecto (integración del repositorio).

Cada capa la mantiene un integrante distinto. Estas pruebas fallan apenas un cambio en una
capa rompe a otra, antes de llegar a la demo:

- Modelo de Alexa (alexa/)            <->  manejadores de la Lambda (lambda/vigilante/handlers.py)
- Firmware (include/config.h)         <->  claves del Shadow de la Lambda (lambda/vigilante/config.py)
- Políticas de AWS (aws/)             <->  recursos que usa la Lambda (tabla, prefijo de Things)
- Repositorio (.gitignore, git)       <->  ningún secreto publicado (RNF6)

Las pruebas que dependen del firmware se omiten (SKIPPED) si esa capa todavía no está en el
repositorio, y se activan solas cuando se fusiona.
"""
import importlib
import json
import re
import subprocess
import sys

import pytest

from tests.harness import EVENTS, LAMBDA_DIR, REPO_ROOT, THING_CODE, Harness, build_event
from vigilante import config as lambda_config
from vigilante import speech
from vigilante.config import Settings
from vigilante.link_repository import LinkRepository

ALEXA_MODEL = REPO_ROOT / "alexa" / "interaction-model.es-US.json"
AWS_DIR = REPO_ROOT / "aws"
HANDLERS_SRC = LAMBDA_DIR / "vigilante" / "handlers.py"

# El firmware vive en la raíz del repositorio (platformio.ini, src/, include/).
# Se revisa también firmware/ (estructura de la guía) para detectar una copia duplicada.
FIRMWARE_DIRS = [REPO_ROOT, REPO_ROOT / "firmware"]
BUILTIN_INTENTS = {"AMAZON.CancelIntent", "AMAZON.HelpIntent", "AMAZON.StopIntent",
                   "AMAZON.NavigateHomeIntent", "AMAZON.FallbackIntent"}


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _model():
    return _load_json(ALEXA_MODEL)["interactionModel"]


def _model_intents():
    return {i["name"]: i for i in _model()["languageModel"]["intents"]}


def _handled_intents():
    """Intents que reconocen los manejadores, leídos del código fuente."""
    src = HANDLERS_SRC.read_text(encoding="utf-8")
    names = set(re.findall(r'is_intent_name\("([\w.]+)"\)', src))
    names |= set(re.findall(r'intent_name\s*=\s*"(\w+)"', src))
    names |= set(re.findall(r'"(AMAZON\.\w+)"', src))
    names.discard("")
    return names


def _firmware_file(relative, must_contain=None):
    """Primer archivo del firmware que existe (y contiene `must_contain`, si se indica)."""
    for base in FIRMWARE_DIRS:
        path = base / relative
        if path.is_file() and (must_contain is None
                               or must_contain in path.read_text(encoding="utf-8")):
            return path
    return None


def _firmware_trees():
    """Carpetas que contienen un firmware (src/ con código C++)."""
    return [base for base in FIRMWARE_DIRS
            if (base / "src").is_dir() and any((base / "src").rglob("*.cpp"))]


def _defines(path):
    """#define NOMBRE "texto" | número  ->  {NOMBRE: valor}"""
    values = {}
    pattern = re.compile(r'^\s*#define\s+(\w+)\s+("([^"]*)"|(\d+)\w*)', re.MULTILINE)
    for match in pattern.finditer(path.read_text(encoding="utf-8")):
        name, _, text, number = match.groups()
        values[name] = text if text is not None else int(number)
    return values


# --------------------------------------------------------------------------------------------
# Alexa  <->  Lambda
# --------------------------------------------------------------------------------------------

def test_modelo_de_alexa_es_valido_e_invocacion_correcta():
    model = _model()["languageModel"]
    assert model["invocationName"] == "vigilante inteligente"
    assert model["invocationName"] == model["invocationName"].lower()
    for intent in model["intents"]:
        for sample in intent.get("samples", []):
            slots_used = set(re.findall(r"\{(\w+)\}", sample))
            declared = {s["name"] for s in intent.get("slots", [])}
            assert slots_used <= declared, f"{intent['name']}: '{sample}' usa un slot no declarado"


def test_cada_intent_del_modelo_tiene_manejador_en_la_lambda():
    faltan = set(_model_intents()) - _handled_intents()
    assert not faltan, f"Intents del modelo sin manejador en handlers.py: {faltan}"


def test_cada_manejador_corresponde_a_un_intent_del_modelo():
    sobran = _handled_intents() - set(_model_intents())
    assert not sobran, f"Manejadores para intents que no existen en el modelo: {sobran}"


@pytest.mark.parametrize("intent", sorted(_model_intents()))
def test_ningun_intent_del_modelo_termina_en_error(intent):
    """Cada intent del modelo, enviado como lo haría Alexa, recibe una respuesta válida."""
    h = Harness()
    h.ask("VincularDispositivoIntent", codigo=THING_CODE)
    slots = {"codigo": THING_CODE} if intent == "VincularDispositivoIntent" else None
    text = h.send(build_event(intent=intent, slots=slots))
    assert text
    assert text != speech.ERROR


def test_slot_codigo_es_numerico_obligatorio_y_con_confirmacion():
    intents = _model_intents()
    slot = intents["VincularDispositivoIntent"]["slots"][0]
    assert (slot["name"], slot["type"]) == ("codigo", "AMAZON.NUMBER")
    dialog = {i["name"]: i for i in _model()["dialog"]["intents"]}
    dialog_slot = dialog["VincularDispositivoIntent"]["slots"][0]
    assert dialog_slot["elicitationRequired"] and dialog_slot["confirmationRequired"]


def test_desvincular_pide_confirmacion_como_espera_la_lambda():
    """UnlinkDeviceHandler decide según confirmationStatus: el modelo debe pedir confirmación."""
    dialog = {i["name"]: i for i in _model()["dialog"]["intents"]}
    assert dialog["DesvincularDispositivoIntent"]["confirmationRequired"] is True


def test_todos_los_prompts_referenciados_existen():
    model = _model()
    declared = {p["id"] for p in model["prompts"]}
    used = set()
    for intent in model["dialog"]["intents"]:
        used |= set(intent.get("prompts", {}).values())
        for slot in intent.get("slots", []):
            used |= set(slot.get("prompts", {}).values())
    assert used <= declared


def test_eventos_de_prueba_usan_intents_del_modelo():
    intents = set(_model_intents())
    files = sorted(EVENTS.glob("*.json"))
    assert len(files) >= 8
    for path in files:
        request = _load_json(path)["request"]
        if request["type"] == "IntentRequest":
            assert request["intent"]["name"] in intents, path.name


# --------------------------------------------------------------------------------------------
# Firmware  <->  Lambda (documento Shadow)
# --------------------------------------------------------------------------------------------

def test_hay_un_solo_firmware_en_el_repositorio():
    """Dos árboles de firmware se desincronizan: solo uno se compila y el otro queda muerto."""
    trees = _firmware_trees()
    assert len(trees) <= 1, (
        "Hay más de un firmware: {}. Debe quedar uno solo (la raíz, con platformio.ini)."
        .format(", ".join(str(t.relative_to(REPO_ROOT)) or "." for t in trees)))
    configs = [base / "include" / "config.h" for base in FIRMWARE_DIRS
               if (base / "include" / "config.h").is_file()]
    assert len(configs) <= 1, "Hay más de un config.h: {}".format(
        ", ".join(str(c.relative_to(REPO_ROOT)) for c in configs))


@pytest.fixture
def firmware_config():
    path = _firmware_file("include/config.h", must_contain="KEY_DOOR")
    if path is None:
        pytest.skip("El firmware (include/config.h con las claves del Shadow) no está en el repositorio")
    return _defines(path)


def test_pines_del_circuito(firmware_config):
    """Pines documentados en el circuito (§2.2): PIR en GPIO 27 y servo en GPIO 25."""
    assert firmware_config["PIR_PIN"] == 27
    assert firmware_config["SERVO_PIN"] == 25


def test_tiempo_de_confirmacion_cabe_en_el_limite_de_la_lambda(firmware_config):
    """La separación mínima entre reportes no debe impedir confirmar antes de que la Lambda se rinda."""
    assert firmware_config["REPORT_MIN_GAP_MS"] / 1000 < Settings.confirm_timeout_s


def test_claves_del_shadow_iguales_en_firmware_y_lambda(firmware_config):
    for name in ("KEY_DOOR", "KEY_MOTION", "KEY_DETECTIONS", "KEY_LAST_DETECTION",
                 "KEY_SENSOR_READY"):
        assert firmware_config[name] == getattr(lambda_config, name), name


def test_valores_de_la_puerta_iguales_en_firmware_y_lambda(firmware_config):
    assert firmware_config["DOOR_OPEN"] == lambda_config.DOOR_OPEN
    assert firmware_config["DOOR_CLOSED"] == lambda_config.DOOR_CLOSED


def test_prefijo_de_things_igual_en_firmware_y_lambda(firmware_config):
    assert firmware_config["THING_PREFIX"] == Settings.thing_prefix


def test_latido_compatible_con_aviso_de_desconexion(firmware_config):
    """La Lambda avisa "puede estar desconectado" tras STALE_AFTER_S sin reporte.

    Debe tolerar al menos un latido perdido: STALE_AFTER_S >= 2 x periodo del latido.
    """
    heartbeat_s = firmware_config["REPORT_PERIOD_MS"] / 1000
    assert Settings.stale_after_s >= 2 * heartbeat_s


def test_plantilla_de_secretos_sin_valores_reales():
    path = _firmware_file("include/secrets.example.h")
    if path is None:
        pytest.skip("secrets.example.h aún no está en el repositorio")
    text = path.read_text(encoding="utf-8")
    thing = _defines(path)["THING_NAME"]
    assert thing.startswith(Settings.thing_prefix)
    assert "PEGUE AQU" in text  # marcadores, no certificados reales
    assert not re.search(r"[A-Za-z0-9+/]{60,}", text), "parece contener un certificado real"


# --------------------------------------------------------------------------------------------
# Políticas de AWS  <->  Lambda
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["iot-policy.json", "lambda-role-policy.json",
                                  "dynamodb-table.json"])
def test_configuraciones_aws_sin_id_de_cuenta_real(name):
    text = (AWS_DIR / name).read_text(encoding="utf-8")
    json.loads(text)
    assert not re.search(r"\b\d{12}\b", text), "no se publica el ID de cuenta de AWS"
    if "policy" in name:
        assert "<ACCOUNT_ID>" in text
        assert set(re.findall(r"arn:aws:\w+:([\w-]+):", text)) == {"us-east-2"}


def test_rol_de_la_lambda_tiene_solo_los_permisos_minimos():
    policy = _load_json(AWS_DIR / "lambda-role-policy.json")
    granted = {}
    for statement in policy["Statement"]:
        assert statement["Effect"] == "Allow"
        actions = statement["Action"]
        for action in [actions] if isinstance(actions, str) else actions:
            granted[action] = statement["Resource"]
    assert set(granted) == {
        "iot:GetThingShadow", "iot:UpdateThingShadow", "iot:DescribeThing",
        "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem",
    }
    assert all("*" not in action for action in granted)
    assert granted["iot:DescribeThing"].endswith(":thing/" + Settings.thing_prefix + "*")
    assert granted["dynamodb:GetItem"].endswith(":table/" + Settings.links_table)


def test_politica_del_dispositivo_limitada_a_su_propio_shadow():
    policy = _load_json(AWS_DIR / "iot-policy.json")
    own = "${iot:Connection.Thing.ThingName}"
    actions = set()
    for statement in policy["Statement"]:
        actions.add(statement["Action"])
        resource = statement["Resource"]
        if statement["Action"] == "iot:Connect":
            assert resource.endswith(":client/" + own)
        else:
            assert f"$aws/things/{own}/shadow/" in resource
    assert actions == {"iot:Connect", "iot:Publish", "iot:Subscribe", "iot:Receive"}


class _RecordingDynamoDB:
    def __init__(self):
        self.keys = []

    def get_item(self, TableName, Key, **_):
        self.keys.append((TableName, Key))
        return {}

    def put_item(self, TableName, Item):
        self.keys.append((TableName, {"userId": Item["userId"]}))

    def delete_item(self, TableName, Key):
        self.keys.append((TableName, Key))


def test_tabla_dynamodb_coincide_con_el_repositorio_de_vinculaciones():
    table = _load_json(AWS_DIR / "dynamodb-table.json")
    assert table["TableName"] == Settings.links_table
    assert table["KeySchema"] == [{"AttributeName": "userId", "KeyType": "HASH"}]
    assert table["AttributeDefinitions"] == [{"AttributeName": "userId", "AttributeType": "S"}]

    client = _RecordingDynamoDB()
    repo = LinkRepository(client, table["TableName"])
    repo.get_thing("u")
    repo.save("u", "vigilante-123456")
    repo.delete("u")
    for table_name, key in client.keys:
        assert table_name == table["TableName"]
        assert key == {"userId": {"S": "u"}}


# --------------------------------------------------------------------------------------------
# Empaquetado y punto de entrada de la Lambda
# --------------------------------------------------------------------------------------------

def test_punto_de_entrada_de_lambda_se_importa(monkeypatch):
    """Handler configurado en la consola: lambda_function.lambda_handler (sin access keys)."""
    monkeypatch.setenv("IOT_ENDPOINT", "example-ats.iot.us-east-2.amazonaws.com")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    sys.modules.pop("lambda_function", None)
    module = importlib.import_module("lambda_function")
    assert callable(module.lambda_handler)
    source = (LAMBDA_DIR / "lambda_function.py").read_text(encoding="utf-8")
    assert "aws_access_key_id" not in source and "AKIA" not in source


def test_dependencias_empaquetadas():
    lines = [line.strip() for line in
             (LAMBDA_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    assert any(line.startswith("ask-sdk-core==") for line in lines)
    assert not any(line.startswith(("boto3", "botocore")) for line in lines)


# --------------------------------------------------------------------------------------------
# Seguridad del repositorio (RNF6)
# --------------------------------------------------------------------------------------------

def _tracked_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git no disponible")
    return [line for line in out.splitlines() if line]


def test_gitignore_excluye_secretos():
    rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for rule in ("secrets.h", "*.pem", "*.key", "*.crt", "*.zip"):
        assert any(r.endswith(rule) for r in rules), f".gitignore no excluye {rule}"


def test_ningun_secreto_versionado_en_git():
    forbidden = re.compile(r"(^|/)secrets\.h$|\.(pem|key|crt|zip)$")
    tracked = _tracked_files()
    assert not [f for f in tracked if forbidden.search(f)]
    for name in tracked:
        path = REPO_ROOT / name
        if path.suffix in {".png", ".jpg", ".jpeg", ".pdf", ".gif", ".mp4"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not re.search(r"-----BEGIN (RSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/]{40,}", text), name
        assert not re.search(r"AKIA[0-9A-Z]{16}", text), name
