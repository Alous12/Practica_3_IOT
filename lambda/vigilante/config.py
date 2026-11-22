"""Configuración de la Lambda leída de variables de entorno."""
import os
from dataclasses import dataclass

# Atributos del Device Shadow (deben coincidir con firmware/include/config.h).
KEY_DOOR = "puerta"
KEY_MOTION = "movimiento"
KEY_DETECTIONS = "detecciones"
KEY_LAST_DETECTION = "ultima_deteccion"
KEY_SENSOR_READY = "sensor_listo"
DOOR_OPEN = "abierta"
DOOR_CLOSED = "cerrada"

# Modo de operación y parámetros (desired los escribe la skill; reported, el ESP32).
KEY_MODE = "modo"
KEY_MAX_DETECTIONS = "max_detecciones"
KEY_WINDOW_MIN = "ventana_min"
KEY_ORIGIN = "origen"

MODE_MANUAL = "manual"          # la puerta solo obedece a la voz
MODE_AUTO = "automatico"        # la regla del Edge cierra la puerta al detectar movimiento
MODE_LOCKDOWN = "bloqueo"           # ídem; la puerta no se abre por voz
MODES = (MODE_MANUAL, MODE_AUTO, MODE_LOCKDOWN)
# Modos en los que la regla del Edge cierra la puerta: "abre la puerta" se rechaza.
AUTOLOCK_MODES = (MODE_AUTO, MODE_LOCKDOWN)

MAX_DETECTIONS_MIN = 1
MAX_DETECTIONS_MAX = 20
WINDOW_MINUTES_MIN = 1
WINDOW_MINUTES_MAX = 120

# Quién causó el último cambio (reported.origen). La skill escribe siempre ORIGIN_VOICE.
ORIGIN_VOICE = "voz"
ORIGIN_EDGE = "edge"
ORIGIN_CLOUD = "nube"
ORIGIN_BOOT = "inicio"


@dataclass(frozen=True)
class Settings:
    """Parámetros de la función. Solo IOT_ENDPOINT es obligatorio."""

    iot_endpoint: str
    links_table: str = "vigilante_vinculaciones"
    thing_prefix: str = "vigilante-"
    code_length: int = 6
    confirm_timeout_s: float = 3.0
    poll_interval_s: float = 0.25
    stale_after_s: int = 150

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            iot_endpoint=os.environ["IOT_ENDPOINT"],
            links_table=os.environ.get("LINKS_TABLE", cls.links_table),
            thing_prefix=os.environ.get("THING_PREFIX", cls.thing_prefix),
            confirm_timeout_s=float(os.environ.get("CONFIRM_TIMEOUT_S", cls.confirm_timeout_s)),
            stale_after_s=int(os.environ.get("STALE_AFTER_S", cls.stale_after_s)),
        )
