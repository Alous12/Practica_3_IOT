"""Acceso al registro de AWS IoT Core y al Device Shadow de cada Thing."""
import json
import logging
import time
from typing import Tuple

from botocore.exceptions import ClientError

from .config import KEY_DOOR
from .device_state import DeviceState

logger = logging.getLogger(__name__)


class DeviceGateway:
    """Envuelve los clientes boto3 `iot` (registro) e `iot-data` (Shadow).

    Permisos IAM necesarios sobre arn:aws:iot:<región>:<cuenta>:thing/vigilante-*:
    iot:DescribeThing, iot:GetThingShadow, iot:UpdateThingShadow.
    """

    def __init__(self, iot_client, iot_data_client, poll_interval_s: float = 0.25,
                 clock=time.monotonic, sleep=time.sleep):
        self._iot = iot_client
        self._data = iot_data_client
        self._poll_interval_s = poll_interval_s
        self._clock = clock
        self._sleep = sleep

    def thing_exists(self, thing_name: str) -> bool:
        """RF9: valida que el Thing exista antes de vincularlo."""
        try:
            self._iot.describe_thing(thingName=thing_name)
            return True
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                return False
            raise

    def get_state(self, thing_name: str) -> DeviceState:
        """Lee el Shadow clásico. Si aún no existe, devuelve un estado vacío."""
        try:
            response = self._data.get_thing_shadow(thingName=thing_name)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                return DeviceState()
            raise
        return DeviceState.from_shadow(json.loads(response["payload"].read()))

    def request_door(self, thing_name: str, value: str) -> None:
        """RF5: escribe state.desired.puerta; el dispositivo lo recibe por el tópico delta."""
        payload = {"state": {"desired": {KEY_DOOR: value}}}
        self._data.update_thing_shadow(thingName=thing_name, payload=json.dumps(payload).encode())

    def wait_for_door(self, thing_name: str, value: str, timeout_s: float) -> Tuple[bool, int]:
        """Espera a que reported.puerta == value. Devuelve (confirmado, milisegundos)."""
        start = self._clock()
        while True:
            elapsed = self._clock() - start
            if self.get_state(thing_name).door == value:
                return True, int(elapsed * 1000)
            if elapsed >= timeout_s:
                return False, int(elapsed * 1000)
            self._sleep(self._poll_interval_s)
