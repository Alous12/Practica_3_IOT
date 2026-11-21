"""Vista de solo lectura del documento Shadow del Thing."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .config import (
    KEY_DETECTIONS,
    KEY_DOOR,
    KEY_LAST_DETECTION,
    KEY_MAX_DETECTIONS,
    KEY_MODE,
    KEY_MOTION,
    KEY_ORIGIN,
    KEY_SENSOR_READY,
    KEY_WINDOW_MIN,
)


def _latest_timestamp(metadata: Dict[str, Any]) -> Optional[int]:
    """Mayor `timestamp` dentro de metadata.reported (cuándo reportó por última vez)."""
    latest = None
    for value in metadata.values():
        if isinstance(value, dict):
            ts = value.get("timestamp")
            if isinstance(ts, int):
                latest = ts if latest is None else max(latest, ts)
            else:
                nested = _latest_timestamp(value)
                if nested is not None:
                    latest = nested if latest is None else max(latest, nested)
    return latest


@dataclass
class DeviceState:
    """Estado del objeto inteligente según su Shadow clásico."""

    reported: Dict[str, Any] = field(default_factory=dict)
    desired: Dict[str, Any] = field(default_factory=dict)
    last_report_epoch: Optional[int] = None

    @classmethod
    def from_shadow(cls, shadow: Dict[str, Any]) -> "DeviceState":
        state = shadow.get("state", {})
        metadata = shadow.get("metadata", {}).get("reported", {})
        return cls(
            reported=state.get("reported", {}) or {},
            desired=state.get("desired", {}) or {},
            last_report_epoch=_latest_timestamp(metadata),
        )

    # --- Acceso genérico (cualquier atributo del Shadow) ---

    def reported_value(self, key: str) -> Any:
        return self.reported.get(key)

    def desired_value(self, key: str) -> Any:
        return self.desired.get(key)

    def is_pending(self, key: str) -> bool:
        """True si hay una orden en desired que el dispositivo aún no aplicó.

        Un desired en null (lo borra la regla del Edge al actuar) no es una orden pendiente.
        """
        wanted = self.desired_value(key)
        return wanted is not None and wanted != self.reported_value(key)

    @property
    def has_report(self) -> bool:
        return bool(self.reported)

    # --- Puerta (actuador) ---

    @property
    def door(self) -> Optional[str]:
        return self.reported_value(KEY_DOOR)

    @property
    def desired_door(self) -> Optional[str]:
        return self.desired_value(KEY_DOOR)

    @property
    def door_pending(self) -> bool:
        return self.is_pending(KEY_DOOR)

    # --- PIR (sensor) ---

    @property
    def motion(self) -> Optional[bool]:
        return self.reported_value(KEY_MOTION)

    @property
    def detections(self) -> int:
        return int(self.reported.get(KEY_DETECTIONS, 0))

    @property
    def last_detection_epoch(self) -> int:
        return int(self.reported.get(KEY_LAST_DETECTION, 0) or 0)

    @property
    def sensor_ready(self) -> bool:
        return bool(self.reported.get(KEY_SENSOR_READY, True))

    # --- Modo, parámetros y origen ---

    @property
    def mode(self) -> Optional[str]:
        """Modo que aplica el dispositivo; None si el firmware aún no lo reporta."""
        return self.reported_value(KEY_MODE)

    @property
    def desired_mode(self) -> Optional[str]:
        return self.desired_value(KEY_MODE)

    @property
    def mode_pending(self) -> bool:
        return self.is_pending(KEY_MODE)

    @property
    def target_mode(self) -> Optional[str]:
        """Modo que regirá: el pedido si aún está pendiente, si no el reportado."""
        return self.desired_mode if self.mode_pending else self.mode

    @property
    def max_detections(self) -> Optional[int]:
        return self.reported_value(KEY_MAX_DETECTIONS)

    @property
    def window_min(self) -> Optional[int]:
        return self.reported_value(KEY_WINDOW_MIN)

    @property
    def origin(self) -> Optional[str]:
        """Quién causó el último cambio: "voz", "edge" o "inicio"."""
        return self.reported_value(KEY_ORIGIN)

    def seconds_since_report(self, now_epoch: float) -> Optional[int]:
        if self.last_report_epoch is None:
            return None
        return max(0, int(now_epoch - self.last_report_epoch))
