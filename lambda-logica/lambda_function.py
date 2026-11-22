"""Lambda vigilante-logica: lógica de negocio en la Nube (RF13).

La invoca la regla vigilante_deteccion cada vez que hay una detección nueva
en modo automático. Cuenta en vigilante_historico las detecciones (en modo
automático) de los últimos ventana_min minutos; si llegan a max_detecciones,
escribe en state.desired del Shadow: modo "bloqueo", puerta "cerrada", alarma
"encendida", origen "nube".
Actúa sobre el objeto SOLO a través de desired.

Permisos IAM mínimos: dynamodb:Query sobre vigilante_historico e
iot:UpdateThingShadow sobre thing/vigilante-*.
Variable de entorno obligatoria: IOT_ENDPOINT (sin https://).
"""
import json
import logging
import os
import re
from datetime import datetime, timezone

import boto3

TABLE = os.environ.get("HISTORY_TABLE", "vigilante_historico")
THING_PREFIX = os.environ.get("THING_PREFIX", "vigilante-")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.client("dynamodb")
iot_data = boto3.client("iot-data", endpoint_url="https://" + os.environ["IOT_ENDPOINT"])

LOCKDOWN = {"modo": "bloqueo", "puerta": "cerrada", "alarma": "encendida", "origen": "nube"}


class InvalidTrigger(ValueError):
    """El mensaje de la regla no trae lo necesario para decidir."""


def int_between(value, low, high, name):
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise InvalidTrigger("{} inválido: {!r}".format(name, value))
    return value


def parse(event):
    if not isinstance(event, dict):
        raise InvalidTrigger("el mensaje no es un objeto JSON")
    thing = event.get("thingName")
    if not isinstance(thing, str) or not re.fullmatch(re.escape(THING_PREFIX) + r"\d{6}", thing):
        raise InvalidTrigger("thingName inválido: {!r}".format(thing))
    return {
        "thing": thing,
        "ts": int_between(event.get("ts"), 1, 4_102_444_800, "ts"),
        "modo": event.get("modo"),
        "max": int_between(event.get("max_detecciones"), 1, 20, "max_detecciones"),
        "ventana": int_between(event.get("ventana_min"), 1, 120, "ventana_min"),
    }


def iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def count_previous_detections(thing, ts, window_min):
    """Detecciones en modo automático ANTES de la actual, dentro de la ventana.

    Se excluye el segundo de la detección actual porque la Lambda de
    almacenamiento la guarda al mismo tiempo; la actual se suma aparte.
    """
    kwargs = {
        "TableName": TABLE,
        "KeyConditionExpression": "thingName = :t AND tipo_ts BETWEEN :desde AND :hasta",
        "FilterExpression": "modo = :modo",
        "ExpressionAttributeValues": {
            ":t": {"S": thing},
            ":desde": {"S": "deteccion#" + iso(ts - window_min * 60)},
            ":hasta": {"S": "deteccion#" + iso(ts - 1)},
            ":modo": {"S": "automatico"},
        },
        "Select": "COUNT",
    }
    total = 0
    while True:
        response = dynamodb.query(**kwargs)
        total += response.get("Count", 0)
        if "LastEvaluatedKey" not in response:
            return total
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]


def log(event, **fields):
    logger.info(json.dumps({"evento": event, **fields}, ensure_ascii=False))


def lambda_handler(event, context):
    try:
        trigger = parse(event)
    except InvalidTrigger as error:
        log("descartado", motivo=str(error), mensaje=event)
        return {"accion": "ninguna", "motivo": str(error)}

    if trigger["modo"] != "automatico":  # la regla SQL ya lo filtra; doble seguridad
        log("sin_accion", thing=trigger["thing"], modo=trigger["modo"])
        return {"accion": "ninguna", "modo": trigger["modo"]}

    total = count_previous_detections(trigger["thing"], trigger["ts"], trigger["ventana"]) + 1
    summary = {"thing": trigger["thing"], "detecciones_en_ventana": total,
               "max_detecciones": trigger["max"], "ventana_min": trigger["ventana"]}
    if total < trigger["max"]:
        log("sin_accion", **summary)
        return {"accion": "ninguna", **summary}

    payload = {"state": {"desired": LOCKDOWN}}
    iot_data.update_thing_shadow(thingName=trigger["thing"], payload=json.dumps(payload).encode())
    log("bloqueo_activado", desired=LOCKDOWN, **summary)
    return {"accion": "bloqueo", "desired": LOCKDOWN, **summary}
