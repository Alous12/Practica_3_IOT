"""Construcción de la skill: registra interceptor, manejadores y dependencias."""
import time
from typing import Callable

from ask_sdk_core.skill_builder import SkillBuilder

from . import handlers as h
from .config import Settings
from .device_gateway import DeviceGateway
from .link_repository import LinkRepository


def build_skill(repository: LinkRepository, gateway: DeviceGateway, settings: Settings,
                now: Callable[[], float] = time.time):
    """Devuelve el SkillBuilder configurado (las dependencias se inyectan para poder probarlo)."""
    sb = SkillBuilder()
    sb.add_global_request_interceptor(h.LinkedThingInterceptor(repository))

    sb.add_request_handler(h.LaunchRequestHandler())
    sb.add_request_handler(h.LinkDeviceHandler(repository, gateway, settings))
    sb.add_request_handler(h.LinkStatusHandler(settings))
    sb.add_request_handler(h.UnlinkDeviceHandler(repository))
    sb.add_request_handler(h.MotionQueryHandler(gateway, settings, now))
    sb.add_request_handler(h.CloseDoorHandler(gateway, settings, now))
    sb.add_request_handler(h.OpenDoorHandler(gateway, settings, now))
    sb.add_request_handler(h.DoorStatusHandler(gateway, settings, now))
    sb.add_request_handler(h.HelpIntentHandler())
    sb.add_request_handler(h.CancelOrStopIntentHandler())
    sb.add_request_handler(h.FallbackIntentHandler())
    sb.add_request_handler(h.SessionEndedRequestHandler())

    sb.add_exception_handler(h.CatchAllExceptionHandler())
    return sb
