"""Vista de solo lectura del documento Shadow del Thing."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .config import (
    KEY_DETECTIONS,
    KEY_DOOR,
    KEY_LAST_DETECTION,
    KEY_MOTION,
    KEY_SENSOR_READY,
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

    @property
    def has_report(self) -> bool:
        return bool(self.reported)

    @property
    def door(self) -> Optional[str]:
        return self.reported.get(KEY_DOOR)

    @property
    def desired_door(self) -> Optional[str]:
        return self.desired.get(KEY_DOOR)

    @property
    def door_pending(self) -> bool:
        """True si hay una orden en desired que el dispositivo aún no aplicó."""
        return self.desired_door is not None and self.desired_door != self.door

    @property
    def motion(self) -> Optional[bool]:
        return self.reported.get(KEY_MOTION)

    @property
    def detections(self) -> int:
        return int(self.reported.get(KEY_DETECTIONS, 0))

    @property
    def last_detection_epoch(self) -> int:
        return int(self.reported.get(KEY_LAST_DETECTION, 0) or 0)

    @property
    def sensor_ready(self) -> bool:
        return bool(self.reported.get(KEY_SENSOR_READY, True))

    def seconds_since_report(self, now_epoch: float) -> Optional[int]:
        if self.last_report_epoch is None:
            return None
        return max(0, int(now_epoch - self.last_report_epoch))
