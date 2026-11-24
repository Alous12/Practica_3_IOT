# Lambda `vigilante-almacenamiento`: procesamiento y almacenamiento (RF10–RF12)

Valida, enriquece y guarda en DynamoDB las lecturas y los eventos del objeto inteligente. **No decide nada ni toca el Shadow**: la lógica de negocio está en [`vigilante-logica`](../lambda-logica/). Diseño completo en el [informe de la Práctica 4](../docs/INFORME_P4.md), §2.4.3 y §2.9.3.

| Archivo | Qué es | Dónde se usa en AWS |
|---|---|---|
| [`lambda_function.py`](lambda_function.py) | Código de la función (`Handler: lambda_function.lambda_handler`, Python 3.13) | Lambda → `vigilante-almacenamiento` → pestaña *Code* |
| [`../aws/almacenamiento-role-policy.json`](../aws/almacenamiento-role-policy.json) | Permiso mínimo: `dynamodb:PutItem` sobre `vigilante_historico` | IAM → rol de `vigilante-almacenamiento` |
| [`events/`](events/) | Mensajes de ejemplo de las reglas | Lambda → pestaña *Test* |
| [`tests/test_storage.py`](tests/test_storage.py) | Pruebas sin acceso a AWS | Local y GitHub Actions |

## Cuándo se ejecuta

| Regla de AWS IoT | Tópico | Mensaje que recibe |
|---|---|---|
| [`vigilante_lecturas`](../aws/iot-rules/vigilante_lecturas.sql) | `$aws/things/+/shadow/update/accepted` | `tipo: "lectura"`, `thingName`, `ts` (ms) y `reported` |
| [`vigilante_eventos`](../aws/iot-rules/vigilante_eventos.sql) | `$aws/things/+/shadow/update/documents` | `tipo: "cambio"`, `thingName`, `ts` (s), `anterior` y `actual`; solo si cambió `puerta`, `modo` o `alarma`, o si subió `detecciones` |

## Qué hace

1. **Valida** el `thingName` (`vigilante-` + 6 dígitos), el `ts` y el tipo y rango de cada atributo conocido (`puerta` ∈ {abierta, cerrada}, `alarma` ∈ {encendida, apagada}, `modo`, `origen`, `max_detecciones` 1–20, `ventana_min` 1–120, …). Si algo no cuadra, registra `descartado` con el motivo y **no escribe nada**.
2. **Enriquece** cada registro con `tipo`, `fecha` ISO UTC, `epoch`, la clave `tipo_ts = <tipo>#<fecha>` y `expira = epoch + TTL_DAYS · 86 400`.
3. **Guarda** con `PutItem` en `vigilante_historico`: una fila `lectura#…` por lectura, y por cada cambio una fila `puerta#…`, `modo#…` o `alarma#…` (con el valor `anterior` y el `origen`) más una `deteccion#…` si subió el contador.

| Evento de prueba | Resultado |
|---|---|
| [`01_lectura.json`](events/01_lectura.json) | `guardados: 1`, clave `lectura#2026-11-20T10:15:42.318Z` |
| [`02_cambio_alarma.json`](events/02_cambio_alarma.json) | `guardados: 2`, claves `alarma#2026-11-20T10:15:42Z` y `deteccion#2026-11-20T10:15:42Z` |
| [`03_lectura_invalida.json`](events/03_lectura_invalida.json) | `descartado: true`, motivo `puerta inválido: 'rota'` |

## Configuración en AWS

| Dato | Valor |
|---|---|
| Nombre | `vigilante-almacenamiento` (Python 3.13), handler `lambda_function.lambda_handler`, tiempo de espera 10 s |
| Disparadores | Reglas `vigilante_lecturas` y `vigilante_eventos` (la consola agrega el permiso de invocación al crear cada acción) |
| Variables de entorno | Opcionales: `HISTORY_TABLE` (`vigilante_historico`), `THING_PREFIX` (`vigilante-`), `TTL_DAYS` (30) |
| Tabla | [`vigilante_historico`](../aws/dynamodb-historico.json) con TTL activado en `expira` ([`dynamodb-historico-ttl.json`](../aws/dynamodb-historico-ttl.json)) |

Solo usa la biblioteca estándar y `boto3`, que ya viene en Lambda: se pega `lambda_function.py` en el editor de la consola y se pulsa **Deploy**.

## Pruebas

```bash
python -m pytest -v lambda-almacenamiento/tests    # desde la raíz del repositorio
```

Reemplazan el cliente de DynamoDB por un doble: no necesitan cuenta de AWS ni credenciales, solo `boto3` y `pytest`.
