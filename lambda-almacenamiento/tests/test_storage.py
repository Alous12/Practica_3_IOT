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


if __name__ == "__main__":
    unittest.main()
