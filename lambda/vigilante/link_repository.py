"""Persistencia de la vinculación usuario de Alexa <-> Thing en DynamoDB."""
from datetime import datetime, timezone
from typing import Optional


class LinkRepository:
    """Tabla con clave de partición `userId` (String) y atributos `thingName`, `fechaVinculacion`.

    Permisos IAM necesarios: dynamodb:GetItem, dynamodb:PutItem, dynamodb:DeleteItem.
    """

    def __init__(self, dynamodb_client, table_name: str):
        self._db = dynamodb_client
        self._table = table_name

    def get_thing(self, user_id: str) -> Optional[str]:
        """Devuelve el thingName vinculado al usuario, o None si no tiene."""
        response = self._db.get_item(
            TableName=self._table,
            Key={"userId": {"S": user_id}},
            ConsistentRead=True,
        )
        item = response.get("Item")
        return item["thingName"]["S"] if item else None

    def save(self, user_id: str, thing_name: str) -> None:
        """Crea o reemplaza (cambio de vinculación) el registro del usuario."""
        self._db.put_item(
            TableName=self._table,
            Item={
                "userId": {"S": user_id},
                "thingName": {"S": thing_name},
                "fechaVinculacion": {"S": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
            },
        )

    def delete(self, user_id: str) -> None:
        self._db.delete_item(TableName=self._table, Key={"userId": {"S": user_id}})
