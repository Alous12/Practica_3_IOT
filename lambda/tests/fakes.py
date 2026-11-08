"""Dobles de prueba de los clientes boto3 (sin acceso a AWS)."""
import io
import json

from botocore.exceptions import ClientError


def _not_found(operation):
    return ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "no existe"}},
                       operation)


class FakeDynamoDB:
    def __init__(self):
        self.items = {}

    def get_item(self, TableName, Key, ConsistentRead=False):
        item = self.items.get(Key["userId"]["S"])
        return {"Item": item} if item else {}

    def put_item(self, TableName, Item):
        self.items[Item["userId"]["S"]] = Item

    def delete_item(self, TableName, Key):
        self.items.pop(Key["userId"]["S"], None)


class FakeIot:
    def __init__(self, things):
        self.things = set(things)

    def describe_thing(self, thingName):
        if thingName not in self.things:
            raise _not_found("DescribeThing")
        return {"thingName": thingName}


class FakeIotData:
    """Shadow en memoria que imita a AWS IoT y al ESP32.

    Si el Thing está en línea (`device_online` y no está en `offline_things`), el
    "dispositivo" aplica el desired y lo confirma en reported tras `lag_polls` lecturas,
    igual que el ESP32 al recibir el delta.
    """

    def __init__(self, now=1_800_000_000, device_online=True, lag_polls=2, offline_things=()):
        self.shadows = {}
        self.now = now
        self.device_online = device_online
        self.offline_things = set(offline_things)
        self.lag_polls = lag_polls
        self._pending_polls = {}

    def is_online(self, thing):
        return self.device_online and thing not in self.offline_things

    def reconnect(self, thing):
        """Simula que el ESP32 vuelve a conectarse: pide shadow/get y aplica el delta pendiente."""
        self.offline_things.discard(thing)
        desired = self.shadows.get(thing, {}).get("state", {}).get("desired", {})
        if desired:
            self.set_reported(thing, **desired)

    def set_reported(self, thing, **reported):
        shadow = self.shadows.setdefault(thing, {"state": {}, "metadata": {}})
        shadow["state"].setdefault("reported", {}).update(reported)
        meta = shadow["metadata"].setdefault("reported", {})
        for key in reported:
            meta[key] = {"timestamp": self.now}

    def get_thing_shadow(self, thingName):
        if thingName not in self.shadows:
            raise _not_found("GetThingShadow")
        if thingName in self._pending_polls:
            self._pending_polls[thingName] -= 1
            if self._pending_polls[thingName] <= 0:
                del self._pending_polls[thingName]
                desired = self.shadows[thingName]["state"].get("desired", {})
                self.set_reported(thingName, **desired)
        return {"payload": io.BytesIO(json.dumps(self.shadows[thingName]).encode())}

    def update_thing_shadow(self, thingName, payload):
        body = json.loads(payload)
        shadow = self.shadows.setdefault(thingName, {"state": {}, "metadata": {}})
        shadow["state"].setdefault("desired", {}).update(body["state"]["desired"])
        if self.is_online(thingName):
            self._pending_polls[thingName] = self.lag_polls
        return {"payload": io.BytesIO(b"{}")}
