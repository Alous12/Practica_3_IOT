"""Pruebas sin AWS de vigilante-logica: reemplazan DynamoDB e IoT Data, no la lógica."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

# Nombre único: no debe chocar con lambda/lambda_function.py (la skill).
with patch("boto3.client"), patch.dict(os.environ, {"IOT_ENDPOINT": "example-ats.iot.us-east-2.amazonaws.com"}):
    spec = importlib.util.spec_from_file_location(
        "vigilante_logica_p4", Path(__file__).resolve().parents[1] / "lambda_function.py"
    )
    logica = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logica)

LOCKDOWN = {"modo": "bloqueo", "puerta": "cerrada", "alarma": "encendida", "origen": "nube"}


class LogicTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.query.return_value = {"Count": 0}
        self.iot = Mock()
        for name, double in (("dynamodb", self.db), ("iot_data", self.iot)):
            patcher = patch.object(logica, name, double)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.trigger = {"thingName": "vigilante-123456", "ts": 1795169742, "modo": "automatico",
                        "max_detecciones": 3, "ventana_min": 10}

    def test_primera_deteccion_no_bloquea(self):
        result = logica.lambda_handler(self.trigger, None)
        self.assertEqual(result["accion"], "ninguna")
        self.assertEqual(result["detecciones_en_ventana"], 1)
        self.iot.update_thing_shadow.assert_not_called()

    def test_dos_anteriores_mas_la_actual_llegan_al_maximo_y_bloquean(self):
        self.db.query.return_value = {"Count": 2}
        result = logica.lambda_handler(self.trigger, None)
        self.assertEqual(result["accion"], "bloqueo")
        self.assertEqual(result["detecciones_en_ventana"], 3)
        self.assertEqual(result["desired"], LOCKDOWN)
        kwargs = self.iot.update_thing_shadow.call_args.kwargs
        self.assertEqual(kwargs["thingName"], "vigilante-123456")
        self.assertEqual(json.loads(kwargs["payload"]), {"state": {"desired": LOCKDOWN}})

    def test_consulta_con_query_count_y_ventana_hasta_ts_menos_1(self):
        logica.lambda_handler(self.trigger, None)
        self.db.scan.assert_not_called()
        query = self.db.query.call_args.kwargs
        self.assertEqual(query["TableName"], "vigilante_historico")
        self.assertEqual(query["Select"], "COUNT")
        values = query["ExpressionAttributeValues"]
        self.assertEqual(values[":t"], {"S": "vigilante-123456"})
        self.assertEqual(values[":desde"], {"S": "deteccion#2026-11-20T10:05:42Z"})
        self.assertEqual(values[":hasta"], {"S": "deteccion#2026-11-20T10:15:41Z"})
        self.assertEqual(values[":modo"], {"S": "automatico"})

    def test_pagina_con_last_evaluated_key(self):
        page_key = {"thingName": {"S": "vigilante-123456"}, "tipo_ts": {"S": "deteccion#x"}}
        self.db.query.side_effect = [{"Count": 1, "LastEvaluatedKey": page_key}, {"Count": 1}]
        result = logica.lambda_handler(self.trigger, None)
        self.assertEqual(self.db.query.call_count, 2)
        self.assertEqual(self.db.query.call_args_list[1].kwargs["ExclusiveStartKey"], page_key)
        self.assertEqual(result["detecciones_en_ventana"], 3)
        self.assertEqual(result["accion"], "bloqueo")

    def test_modo_manual_no_consulta_ni_escribe(self):
        event = {**self.trigger, "modo": "manual"}
        self.assertEqual(logica.lambda_handler(event, None)["accion"], "ninguna")
        self.db.query.assert_not_called()
        self.iot.update_thing_shadow.assert_not_called()

    def test_mensajes_invalidos_se_descartan_sin_escribir(self):
        invalid = (
            ("thingName", "vigilante-X"), ("max_detecciones", True), ("max_detecciones", 21),
            ("ventana_min", 0), ("ts", "1795169742"),
        )
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                event = copy.deepcopy(self.trigger)
                event[key] = value
                result = logica.lambda_handler(event, None)
                self.assertEqual(result["accion"], "ninguna")
                self.assertIn("inválido", result["motivo"])
        self.assertEqual(logica.lambda_handler(None, None)["accion"], "ninguna")
        self.db.query.assert_not_called()
        self.iot.update_thing_shadow.assert_not_called()


if __name__ == "__main__":
    unittest.main()
