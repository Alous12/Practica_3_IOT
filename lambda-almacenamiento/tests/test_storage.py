"""Pruebas sin AWS: reemplazan el cliente DynamoDB, no la logica de validacion."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

with patch("boto3.client") as client:
    spec = importlib.util.spec_from_file_location(
        "storage_p4", Path(__file__).resolve().parents[1] / "lambda_function.py"
    )
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.client = patch.object(storage, "dynamodb", self.db)
        self.client.start()
        self.addCleanup(self.client.stop)
        self.state = {"movimiento": True, "detecciones": 4,
                      "puerta": "cerrada", "modo": "automatico", "origen": "edge"}
        self.reading = {"tipo": "lectura", "thingName": "vigilante-123456",
                        "ts": 1795169742123, "reported": self.state}

    def test_valid_reading_keys_ttl_and_typed_data(self):
        result = storage.lambda_handler(self.reading, None)
        self.assertEqual(result["guardados"], 1)
        item = self.db.put_item.call_args.kwargs["Item"]
        self.assertEqual(item["tipo_ts"], {"S": "lectura#2026-11-20T10:15:42.123Z"})
        self.assertEqual(item["expira"], {"N": str(1795169742 + 30 * 86400)})
        self.assertEqual(item["movimiento"], {"BOOL": True})
        self.assertEqual(self.db.put_item.call_args.kwargs["TableName"], "vigilante_historico")

    def test_invalid_values_never_write(self):
        for key, value in (("puerta", "rota"), ("detecciones", True),
                           ("max_detecciones", 21), ("ventana_min", 0),
                           ("modo", "otro"), ("origen", "desconocido")):
            with self.subTest(key=key):
                event = copy.deepcopy(self.reading)
                event["reported"][key] = value
                self.assertTrue(storage.lambda_handler(event, None)["descartado"])
        self.db.put_item.assert_not_called()

    def test_missing_or_malformed_message(self):
        for event in (None, {}, {**self.reading, "thingName": "vigilante-X"},
                      {**self.reading, "ts": True}, {**self.reading, "reported": {}}):
            with self.subTest(event=event):
                self.assertTrue(storage.lambda_handler(event, None)["descartado"])
        self.db.put_item.assert_not_called()

    def test_changes_record_door_mode_and_detection(self):
        previous = {**self.state, "puerta": "abierta", "modo": "manual", "detecciones": 3}
        event = {"tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
                 "anterior": previous, "actual": self.state}
        result = storage.lambda_handler(event, None)
        self.assertEqual(result["guardados"], 3)
        records = storage.event_records(event)
        self.assertEqual([r["tipo"] for r in records], ["puerta", "modo", "deteccion"])
        self.assertEqual(records[0]["origen"], "edge")
        self.assertEqual(records[0]["anterior"], "abierta")

    def test_heartbeat_and_restart_are_not_new_detections(self):
        event = {"tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
                 "anterior": self.state, "actual": dict(self.state)}
        self.assertEqual(storage.lambda_handler(event, None)["guardados"], 0)
        event["actual"]["detecciones"] = 0
        self.assertEqual(storage.lambda_handler(event, None)["guardados"], 0)
        self.db.put_item.assert_not_called()

    def test_database_error_is_not_reported_as_success(self):
        self.db.put_item.side_effect = RuntimeError("DynamoDB no disponible")
        with self.assertRaises(RuntimeError):
            storage.lambda_handler(self.reading, None)

    def test_alarm_example_records_alarm_and_detection(self):
        event = {
            "tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
            "anterior": {"movimiento": False, "detecciones": 4,
                         "puerta": "cerrada", "modo": "bloqueo", "alarma": "apagada"},
            "actual": {"movimiento": True, "detecciones": 5,
                       "puerta": "cerrada", "modo": "bloqueo", "alarma": "encendida",
                       "origen": "edge"},
        }
        result = storage.lambda_handler(event, None)
        self.assertEqual(result["claves"], ["alarma#2026-11-20T10:15:42Z",
                                          "deteccion#2026-11-20T10:15:42Z"])
        self.assertEqual(result["guardados"], 2)
        alarm = self.db.put_item.call_args_list[0].kwargs["Item"]
        self.assertEqual(alarm["alarma"], {"S": "encendida"})
        self.assertEqual(alarm["anterior"], {"S": "apagada"})
        self.assertEqual(alarm["origen"], {"S": "edge"})

    def test_alarm_turn_off_retains_each_origin(self):
        for origin in ("voz", "edge", "nube"):
            with self.subTest(origin=origin):
                self.db.reset_mock()
                event = {
                    "tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
                    "anterior": {**self.state, "alarma": "encendida"},
                    "actual": {**self.state, "alarma": "apagada", "origen": origin},
                }
                result = storage.lambda_handler(event, None)
                self.assertEqual(result["guardados"], 1)
                item = self.db.put_item.call_args.kwargs["Item"]
                self.assertEqual(item["tipo"], {"S": "alarma"})
                self.assertEqual(item["alarma"], {"S": "apagada"})
                self.assertEqual(item["anterior"], {"S": "encendida"})
                self.assertEqual(item["origen"], {"S": origin})

    def test_invalid_alarm_is_discarded_without_writes(self):
        reading = {**self.reading, "reported": {**self.state, "alarma": "rota"}}
        event = {
            "tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
            "anterior": {**self.state, "alarma": "apagada"},
            "actual": {**self.state, "alarma": "rota"},
        }
        for message in (reading, event):
            with self.subTest(tipo=message["tipo"]):
                result = storage.lambda_handler(message, None)
                self.assertTrue(result["descartado"])
                self.assertEqual(result["guardados"], 0)
                self.assertIn("alarma", result["motivo"])
        self.db.put_item.assert_not_called()

    def test_alarm_is_optional_for_older_firmware(self):
        result = storage.lambda_handler(self.reading, None)
        self.assertFalse(result["descartado"])
        self.assertEqual(result["guardados"], 1)
        self.assertNotIn("alarma", self.db.put_item.call_args.kwargs["Item"])

    def test_unchanged_alarm_does_not_create_event(self):
        state = {**self.state, "alarma": "encendida"}
        event = {
            "tipo": "cambio", "thingName": "vigilante-123456", "ts": 1795169742,
            "anterior": state, "actual": dict(state),
        }
        result = storage.lambda_handler(event, None)
        self.assertFalse(result["descartado"])
        self.assertEqual(result["guardados"], 0)
        self.db.put_item.assert_not_called()

    def test_reading_preserves_valid_alarm_state(self):
        for alarm in ("encendida", "apagada"):
            with self.subTest(alarma=alarm):
                message = {**self.reading, "reported": {**self.state, "alarma": alarm}}
                self.assertEqual(storage.lambda_handler(message, None)["guardados"], 1)
                self.assertEqual(self.db.put_item.call_args.kwargs["Item"]["alarma"], {"S": alarm})


if __name__ == "__main__":
    unittest.main()
