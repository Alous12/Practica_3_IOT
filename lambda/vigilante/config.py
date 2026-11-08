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
