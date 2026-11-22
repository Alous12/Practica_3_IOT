"""Pruebas de vigilante-logica (regla de la Nube, RF13) sin acceso a AWS.

El módulo se importa desde su ruta (lambda/ también tiene un lambda_function.py) y sus
clientes de AWS se reemplazan por dobles. El doble de DynamoDB evalúa la consulta igual
que la tabla vigilante_historico: mismo thingName, tipo_ts entre :desde y :hasta
(BETWEEN incluye los extremos) y filtro modo = :modo.
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

LOGIC_DIR = Path(__file__).resolve().parents[1]
THING = "vigilante-482917"
TS = 1795169742  # 2026-11-20T10:15:42Z, igual que events/01_deteccion_automatico.json
LOCKDOWN = {"modo": "bloqueo", "puerta": "cerrada", "alarma": "encendida", "origen": "nube"}


def deteccion(seconds_before, modo="automatico", thing=THING):
    """Ítem como lo guarda vigilante-almacenamiento: tipo_ts = deteccion#<ISO UTC al segundo>."""
    moment = datetime.fromtimestamp(TS - seconds_before, tz=timezone.utc)
    return {"thingName": thing, "tipo_ts": "deteccion#" + moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "modo": modo}


class FakeDynamoDB:
    """Evalúa la consulta sobre una lista de ítems; page_size simula la paginación."""

    def __init__(self, items=(), page_size=None):
        self.items = list(items)
        self.page_size = page_size
        self.queries = []

    def query(self, **kwargs):
        self.queries.append(kwargs)
        assert kwargs["TableName"] == "vigilante_historico"
        assert kwargs["KeyConditionExpression"] == \
            "thingName = :t AND tipo_ts BETWEEN :desde AND :hasta"
        assert kwargs["FilterExpression"] == "modo = :modo"
        assert kwargs["Select"] == "COUNT"
        values = {name: value["S"] for name, value in kwargs["ExpressionAttributeValues"].items()}
        in_key = sorted((item for item in self.items
                         if item["thingName"] == values[":t"]
                         and values[":desde"] <= item["tipo_ts"] <= values[":hasta"]),
                        key=lambda item: item["tipo_ts"])
        start = kwargs.get("ExclusiveStartKey", {}).get("pos", 0)
        end = len(in_key) if self.page_size is None else start + self.page_size
        page = in_key[start:end]
        response = {"Count": sum(1 for item in page if item["modo"] == values[":modo"])}
        if end < len(in_key):
            response["LastEvaluatedKey"] = {"pos": end}
        return response


class FakeIotData:
    def __init__(self):
        self.updates = []

    def update_thing_shadow(self, thingName, payload):
        self.updates.append((thingName, json.loads(payload)))
        return {"payload": b"{}"}


@pytest.fixture
def logic(monkeypatch):
    monkeypatch.setenv("IOT_ENDPOINT", "example-ats.iot.us-east-2.amazonaws.com")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    spec = importlib.util.spec_from_file_location("vigilante_logica",
                                                  LOGIC_DIR / "lambda_function.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.dynamodb = FakeDynamoDB()
    module.iot_data = FakeIotData()
    return module


def trigger(**changes):
    event = {"thingName": THING, "ts": TS, "detecciones": 4, "modo": "automatico",
             "max_detecciones": 3, "ventana_min": 10}
    event.update(changes)
    return event


def test_sin_detecciones_previas_no_actua(logic):
    result = logic.lambda_handler(trigger(), None)
    assert result["accion"] == "ninguna"
    assert result["detecciones_en_ventana"] == 1
    assert logic.iot_data.updates == []


def test_dos_previas_mas_la_actual_activan_el_bloqueo(logic):
    logic.dynamodb.items = [deteccion(60), deteccion(300)]
    result = logic.lambda_handler(trigger(), None)
    assert result["accion"] == "bloqueo"
    assert result["detecciones_en_ventana"] == 3
    assert result["desired"] == LOCKDOWN
    assert logic.iot_data.updates == [(THING, {"state": {"desired": LOCKDOWN}})]


def test_fuera_de_ventana_en_manual_o_de_otro_thing_no_cuentan(logic):
    logic.dynamodb.items = [
        deteccion(60),                              # cuenta
        deteccion(11 * 60),                         # hace 11 min: fuera de la ventana
        deteccion(120, modo="manual"),              # dentro, pero en modo manual
        deteccion(90, thing="vigilante-000001"),    # otro objeto
    ]
    result = logic.lambda_handler(trigger(), None)
    assert result["accion"] == "ninguna"
    assert result["detecciones_en_ventana"] == 2
    assert logic.iot_data.updates == []


def test_el_borde_de_la_ventana_cuenta(logic):
    logic.dynamodb.items = [deteccion(10 * 60), deteccion(1)]
    result = logic.lambda_handler(trigger(), None)
    assert result["accion"] == "bloqueo" and result["detecciones_en_ventana"] == 3


def test_la_deteccion_del_mismo_segundo_no_se_cuenta_dos_veces(logic):
    """vigilante-almacenamiento guarda la detección actual con el mismo ts."""
    logic.dynamodb.items = [deteccion(0), deteccion(30)]
    result = logic.lambda_handler(trigger(), None)
    assert result["detecciones_en_ventana"] == 2
    assert result["accion"] == "ninguna"


def test_suma_todas_las_paginas_de_la_consulta(logic):
    logic.dynamodb = FakeDynamoDB([deteccion(s) for s in (10, 20, 30, 40, 50)], page_size=2)
    result = logic.lambda_handler(trigger(max_detecciones=6), None)
    assert len(logic.dynamodb.queries) == 3
    assert result["detecciones_en_ventana"] == 6 and result["accion"] == "bloqueo"


def test_modo_manual_no_consulta_dynamodb(logic):
    result = logic.lambda_handler(trigger(modo="manual"), None)
    assert result == {"accion": "ninguna", "modo": "manual"}
    assert logic.dynamodb.queries == []
    assert logic.iot_data.updates == []


@pytest.mark.parametrize("changes", [
    {"thingName": "otro-1"},
    {"max_detecciones": 0},
    {"ventana_min": 500},
    {"ts": "ayer"},
    {"max_detecciones": True},
])
def test_mensajes_invalidos_se_descartan_sin_consultar_ni_escribir(logic, changes):
    result = logic.lambda_handler(trigger(**changes), None)
    assert result["accion"] == "ninguna" and "motivo" in result
    assert logic.dynamodb.queries == []
    assert logic.iot_data.updates == []


def test_mensaje_que_no_es_objeto_se_descarta(logic):
    assert logic.lambda_handler(["no", "es", "objeto"], None)["accion"] == "ninguna"
    assert logic.lambda_handler(None, None)["accion"] == "ninguna"
    assert logic.dynamodb.queries == []


def test_eventos_de_prueba_de_la_consola(logic):
    """Los mismos eventos que se pegan en la pestaña Test de la consola de Lambda."""
    automatic = json.loads((LOGIC_DIR / "events" / "01_deteccion_automatico.json")
                           .read_text(encoding="utf-8"))
    manual = json.loads((LOGIC_DIR / "events" / "02_deteccion_manual.json")
                        .read_text(encoding="utf-8"))
    logic.dynamodb.items = [deteccion(60), deteccion(120)]
    assert logic.lambda_handler(manual, None)["accion"] == "ninguna"
    assert logic.lambda_handler(automatic, None)["accion"] == "bloqueo"


def test_sin_access_keys_en_el_codigo():
    source = (LOGIC_DIR / "lambda_function.py").read_text(encoding="utf-8")
    assert "aws_access_key_id" not in source and "AKIA" not in source
