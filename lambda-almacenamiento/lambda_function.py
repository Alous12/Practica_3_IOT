"""RF10-RF12: valida y almacena lecturas/eventos; no modifica el Shadow.

Entradas: tipo=lectura (reported, ts en ms) o tipo=cambio (anterior/actual,
ts en segundos), ambas con thingName. Credenciales mediante el rol de Lambda.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.types import TypeSerializer

TABLE = os.environ.get("HISTORY_TABLE", "vigilante_historico")
THING_PREFIX = os.environ.get("THING_PREFIX", "vigilante-")
TTL_DAYS = int(os.environ.get("TTL_DAYS", "30"))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.client("dynamodb")
serializer = TypeSerializer()


class InvalidMessage(ValueError):
    """Mensaje invalido: se descarta sin escribir en DynamoDB."""


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def int_between(low, high):
    return lambda value: is_int(value) and low <= value <= high


def one_of(*options):
    return lambda value: isinstance(value, str) and value in options


FIELDS = {
    "movimiento": lambda value: isinstance(value, bool),
    "detecciones": int_between(0, 10_000_000),
    "ultima_deteccion": int_between(0, 4_102_444_800),
    "sensor_listo": lambda value: isinstance(value, bool),
    "puerta": one_of("abierta", "cerrada"),
    "modo": one_of("manual", "automatico", "bloqueo"),
    "max_detecciones": int_between(1, 20),
    "ventana_min": int_between(1, 120),
    "origen": one_of("voz", "edge", "nube", "inicio"),
    "alarma": one_of("encendida", "apagada"),
    "uptime_s": int_between(0, 10_000_000_000),
    "rssi": int_between(-120, 0),
}
REQUIRED = ("movimiento", "detecciones", "puerta")


def validate_thing(thing):
    pattern = re.escape(THING_PREFIX) + r"\d{6}"
    if not isinstance(thing, str) or not re.fullmatch(pattern, thing):
        raise InvalidMessage("thingName inválido: {!r}".format(thing))
    return thing


def validate_ts(ts):
    if not is_int(ts) or ts <= 0:
        raise InvalidMessage("ts inválido: {!r}".format(ts))
    return ts / 1000 if ts > 10_000_000_000 else ts


def clean(reported, required=REQUIRED):
    if not isinstance(reported, dict):
        raise InvalidMessage("reported no es un objeto JSON")
    result = {}
    for key, rule in FIELDS.items():
        if reported.get(key) is None:
            continue
        if not rule(reported[key]):
            raise InvalidMessage("{} inválido: {!r}".format(key, reported[key]))
        result[key] = reported[key]
    missing = [key for key in required if key not in result]
    if missing:
        raise InvalidMessage("faltan atributos: " + ", ".join(missing))
    return result


def base_record(thing, kind, epoch, millis):
    moment = datetime.fromtimestamp(epoch, tz=timezone.utc)
    fecha = moment.strftime("%Y-%m-%dT%H:%M:%S")
    fecha += ".{:03d}Z".format(moment.microsecond // 1000) if millis else "Z"
    return {
        "thingName": thing,
        "tipo_ts": "{}#{}".format(kind, fecha),
        "tipo": kind,
        "fecha": fecha,
        "epoch": int(epoch),
        "expira": int(epoch) + TTL_DAYS * 86_400,
    }


def reading_records(message):
    thing = validate_thing(message.get("thingName"))
    record = base_record(thing, "lectura", validate_ts(message.get("ts")), millis=True)
    record.update(clean(message.get("reported")))
    return [record]


def event_records(message):
    thing = validate_thing(message.get("thingName"))
    epoch = validate_ts(message.get("ts"))
    if not isinstance(message.get("anterior"), dict):
        raise InvalidMessage("no hay documento anterior")
    before = clean(message["anterior"], required=())
    now = clean(message.get("actual"))
    origin = now.get("origen")
    records = []
    for key in ("puerta", "modo", "alarma"):
        if key in now and key in before and now[key] != before[key]:
            record = base_record(thing, key, epoch, millis=False)
            record.update({key: now[key], "anterior": before[key]})
            if origin:
                record["origen"] = origin
            records.append(record)
    if "detecciones" in before and now["detecciones"] > before["detecciones"]:
        record = base_record(thing, "deteccion", epoch, millis=False)
        record.update({"detecciones": now["detecciones"], "puerta": now["puerta"]})
        if "modo" in now:
            record["modo"] = now["modo"]
        records.append(record)
    return records


def log(event, **fields):
    logger.info(json.dumps({"evento": event, **fields}, ensure_ascii=False, default=str))


def lambda_handler(event, context):
    try:
        if not isinstance(event, dict):
            raise InvalidMessage("el mensaje no es un objeto JSON")
        if event.get("tipo") == "lectura":
            records = reading_records(event)
        elif event.get("tipo") == "cambio":
            records = event_records(event)
        else:
            raise InvalidMessage("tipo desconocido: {!r}".format(event.get("tipo")))
    except InvalidMessage as error:
        log("descartado", motivo=str(error), mensaje=event)
        return {"guardados": 0, "descartado": True, "motivo": str(error)}
    for record in records:
        item = {key: serializer.serialize(value) for key, value in record.items()}
        dynamodb.put_item(TableName=TABLE, Item=item)
        log("guardado", thing=record["thingName"], tipo_ts=record["tipo_ts"])
    return {"guardados": len(records), "descartado": False,
            "claves": [record["tipo_ts"] for record in records]}
