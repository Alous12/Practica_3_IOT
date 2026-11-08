"""Manejadores de la skill (uno por intent) e interceptor de vinculación."""
import json
import logging
import time
from typing import Callable, Optional

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
    AbstractRequestInterceptor,
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from botocore.exceptions import ClientError

from . import speech
from .config import DOOR_CLOSED, DOOR_OPEN, Settings
from .device_gateway import DeviceGateway
from .link_repository import LinkRepository

logger = logging.getLogger(__name__)

THING_ATTR = "thing_name"


def _log_event(event: str, **fields) -> None:
    """Log estructurado (una línea JSON) para usar como evidencia en las pruebas."""
    logger.info(json.dumps({"evento": event, **fields}, ensure_ascii=False))


def _user_id(handler_input: HandlerInput) -> str:
    return handler_input.request_envelope.context.system.user.user_id


def _linked_thing(handler_input: HandlerInput) -> Optional[str]:
    return handler_input.attributes_manager.request_attributes.get(THING_ATTR)


def _ask(handler_input: HandlerInput, text: str, reprompt: str = speech.REPROMPT) -> Response:
    return handler_input.response_builder.speak(text).ask(reprompt).response


class LinkedThingInterceptor(AbstractRequestInterceptor):
    """RF8: en cada solicitud resuelve el Thing vinculado a context.System.user.userId."""

    def __init__(self, repository: LinkRepository):
        self._repository = repository

    def process(self, handler_input: HandlerInput) -> None:
        if not (ask_utils.is_request_type("LaunchRequest")(handler_input)
                or ask_utils.is_request_type("IntentRequest")(handler_input)):
            return
        thing = self._repository.get_thing(_user_id(handler_input))
        handler_input.attributes_manager.request_attributes[THING_ATTR] = thing


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        if _linked_thing(handler_input):
            return _ask(handler_input, speech.WELCOME_LINKED, speech.WELCOME_LINKED)
        return _ask(handler_input, speech.WELCOME_UNLINKED, speech.NOT_LINKED)


class LinkDeviceHandler(AbstractRequestHandler):
    """RF7 y RF9: vincula o cambia la vinculación con el código de 6 dígitos del Thing."""

    def __init__(self, repository: LinkRepository, gateway: DeviceGateway, settings: Settings):
        self._repository = repository
        self._gateway = gateway
        self._settings = settings

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("VincularDispositivoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slot = ask_utils.get_slot(handler_input, "codigo")
        code = (slot.value if slot and slot.value else "").strip()
        if not (code.isdigit() and len(code) == self._settings.code_length):
            return _ask(handler_input,
                        "El código debe tener seis dígitos. Revisa el código que muestra tu "
                        "dispositivo y di: vincula mi dispositivo con el código, seguido de los "
                        "seis dígitos.")

        thing = self._settings.thing_prefix + code
        if not self._gateway.thing_exists(thing):
            _log_event("vinculacion_rechazada", thing=thing, motivo="no_existe")
            return _ask(handler_input,
                        "No encontré ningún dispositivo con el código {}. Revisa el código e "
                        "inténtalo de nuevo.".format(speech.digits(code)))

        user_id = _user_id(handler_input)
        previous = _linked_thing(handler_input)
        if previous == thing:
            return _ask(handler_input, "Ese dispositivo ya estaba vinculado a tu cuenta.")

        self._repository.save(user_id, thing)
        _log_event("vinculacion", thing=thing, anterior=previous)
        if previous:
            old_code = previous[len(self._settings.thing_prefix):]
            text = ("Listo, cambié tu vinculación del dispositivo {} al dispositivo {}."
                    .format(speech.digits(old_code), speech.digits(code)))
        else:
            text = ("Listo, vinculé tu dispositivo {}. Ahora puedes preguntar si hay movimiento "
                    "o pedirme que cierre la puerta.".format(speech.digits(code)))
        return _ask(handler_input, text)


class LinkStatusHandler(AbstractRequestHandler):
    def __init__(self, settings: Settings):
        self._settings = settings

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("ConsultarVinculacionIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        thing = _linked_thing(handler_input)
        if not thing:
            return _ask(handler_input, speech.NOT_LINKED)
        code = thing[len(self._settings.thing_prefix):]
        return _ask(handler_input, "Tienes vinculado el dispositivo {}.".format(speech.digits(code)))


class UnlinkDeviceHandler(AbstractRequestHandler):
    """RF9: elimina la vinculación (Alexa pide confirmación antes, ver modelo de diálogo)."""

    def __init__(self, repository: LinkRepository):
        self._repository = repository

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("DesvincularDispositivoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        if not _linked_thing(handler_input):
            return _ask(handler_input, "No tienes ningún dispositivo vinculado.")
        intent = handler_input.request_envelope.request.intent
        status = getattr(intent.confirmation_status, "value", None)
        if status == "DENIED":
            return _ask(handler_input, "De acuerdo, tu dispositivo sigue vinculado.")
        self._repository.delete(_user_id(handler_input))
        _log_event("desvinculacion", thing=_linked_thing(handler_input))
        return _ask(handler_input,
                    "Listo, desvinculé tu dispositivo. Para volver a usarlo, vincúlalo de nuevo "
                    "con su código.")


class LinkedDeviceHandler(AbstractRequestHandler):
    """Base de los intents que operan sobre el Thing vinculado (RF8)."""

    intent_name = ""

    def __init__(self, gateway: DeviceGateway, settings: Settings,
                 now: Callable[[], float] = time.time):
        self._gateway = gateway
        self._settings = settings
        self._now = now

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name(self.intent_name)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        thing = _linked_thing(handler_input)
        if not thing:
            return _ask(handler_input, speech.NOT_LINKED)
        try:
            return _ask(handler_input, self.handle_linked(thing))
        except ClientError as error:
            logger.error(error, exc_info=True)
            return _ask(handler_input, speech.DEVICE_ERROR)

    def handle_linked(self, thing: str) -> str:
        raise NotImplementedError

    def _stale(self, state) -> str:
        return speech.stale_warning(state.seconds_since_report(self._now()),
                                    self._settings.stale_after_s)


class MotionQueryHandler(LinkedDeviceHandler):
    """RF4: valor actual del sensor PIR leído de state.reported."""

    intent_name = "ConsultarMovimientoIntent"

    def handle_linked(self, thing: str) -> str:
        state = self._gateway.get_state(thing)
        if not state.has_report:
            return speech.NO_REPORT
        if not state.sensor_ready:
            return ("El sensor de movimiento se está calibrando, espera un minuto."
                    + self._stale(state))

        if state.motion:
            text = "¡Atención! Se está detectando movimiento en este momento."
        else:
            text = "No se detecta movimiento en este momento."
        if state.detections and state.last_detection_epoch:
            text += " La última detección fue {}.".format(
                speech.elapsed(int(self._now()) - state.last_detection_epoch))
        text += " Detecciones desde que se encendió: {}.".format(state.detections)
        return text + self._stale(state)


class DoorCommandHandler(LinkedDeviceHandler):
    """RF5: escribe state.desired.puerta y espera la confirmación en reported."""

    target = DOOR_CLOSED
    verb = "cerrar"

    def handle_linked(self, thing: str) -> str:
        current = self._gateway.get_state(thing)
        if current.door == self.target and not current.door_pending:
            return "La puerta ya está {}.".format(self.target) + self._stale(current)

        self._gateway.request_door(thing, self.target)
        confirmed, latency_ms = self._gateway.wait_for_door(
            thing, self.target, self._settings.confirm_timeout_s)
        _log_event("comando_puerta", thing=thing, objetivo=self.target,
                   confirmado=confirmed, latencia_ms=latency_ms)
        if confirmed:
            return "Listo, la puerta quedó {}.".format(self.target)
        return ("Envié la orden de {} la puerta, pero el dispositivo aún no la confirmó. "
                "Se aplicará en cuanto se conecte.".format(self.verb))


class CloseDoorHandler(DoorCommandHandler):
    intent_name = "CerrarPuertaIntent"
    target = DOOR_CLOSED
    verb = "cerrar"


class OpenDoorHandler(DoorCommandHandler):
    intent_name = "AbrirPuertaIntent"
    target = DOOR_OPEN
    verb = "abrir"


class DoorStatusHandler(LinkedDeviceHandler):
    """RF6: estado actual del actuador leído de state.reported."""

    intent_name = "EstadoPuertaIntent"

    def handle_linked(self, thing: str) -> str:
        state = self._gateway.get_state(thing)
        if state.door is None:
            return speech.NO_REPORT
        text = "La puerta está {}.".format(state.door)
        if state.door_pending:
            text += " Hay una orden pendiente para dejarla {}.".format(state.desired_door)
        return text + self._stale(state)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return _ask(handler_input, speech.HELP, speech.HELP)


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Cierra la sesión. NavigateHomeIntent es obligatorio en el modelo (dispositivos con pantalla)."""

    INTENTS = ("AMAZON.CancelIntent", "AMAZON.StopIntent", "AMAZON.NavigateHomeIntent")

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return any(ask_utils.is_intent_name(name)(handler_input) for name in self.INTENTS)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(speech.GOODBYE).set_should_end_session(True).response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return _ask(handler_input, speech.FALLBACK)


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(exception, exc_info=True)
        return _ask(handler_input, speech.ERROR)
