# Lambda `vigilante-logica`: lógica de negocio en la nube (RF13)

Responsable: Rubén.

Decide **en la nube** cuándo el objeto pasa a bloqueo por exceso de detecciones. Actúa sobre el ESP32 **solo a través de `state.desired`** del Device Shadow: nunca le habla directamente.

## Qué hace

La invoca la regla de IoT `vigilante_deteccion` cada vez que hay una detección nueva en modo automático. El mensaje trae `thingName`, `ts` (epoch en segundos), `modo`, `max_detecciones` y `ventana_min`.

1. **Valida el mensaje.** `thingName` debe ser `vigilante-` + 6 dígitos, `ts` un entero positivo, `max_detecciones` entre 1 y 20 y `ventana_min` entre 1 y 120. Si algo falta o está fuera de rango, el mensaje se descarta (`"accion": "ninguna"`) sin escribir nada. Si el `modo` no es `automatico`, tampoco hace nada: la regla SQL ya lo filtra, esto es una doble seguridad.
2. **Cuenta las detecciones de la ventana.** Hace un `Query` (nunca `Scan`) en `vigilante_historico` por la clave `thingName` y el rango de `tipo_ts` entre `deteccion#<ts − ventana_min·60>` y `deteccion#<ts − 1>`. Filtra por `modo = automatico`, pide solo el conteo (`Select: COUNT`) y sigue `LastEvaluatedKey` si la respuesta viene paginada. Al resultado le suma 1, que es la detección actual.
3. **Activa el bloqueo si se llegó al máximo.** Si el total es mayor o igual que `max_detecciones`, escribe en el Shadow:
   ```json
   {"state": {"desired": {"modo": "bloqueo", "puerta": "cerrada", "alarma": "encendida", "origen": "nube"}}}
   ```
   El ESP32 recibe el `delta`, aplica el modo, cierra la puerta, enciende la alarma y reporta `origen: "nube"`.

### Por qué la consulta termina en `ts − 1`

La Lambda de almacenamiento guarda la detección actual en `vigilante_historico` **al mismo tiempo** que se invoca esta Lambda. Según qué termine primero, esa fila puede estar o no en la tabla al momento de la consulta. Para no contarla dos veces (ni olvidarla), la consulta llega solo hasta el segundo anterior (`ts − 1`) y la detección actual se suma siempre aparte con `+1`.

## Configuración en AWS

| Dato | Valor |
|---|---|
| Nombre | `vigilante-logica` (Python 3.13), handler `lambda_function.lambda_handler` |
| Disparador | Regla de IoT `vigilante_deteccion` |
| Tiempo de espera | 10 s |
| Logs | CloudWatch `/aws/lambda/vigilante-logica`, retención de 1 semana. Cada invocación deja una línea JSON: `descartado`, `sin_accion` o `bloqueo_activado` |

### Variables de entorno

| Variable | Obligatoria | Valor |
|---|---|---|
| `IOT_ENDPOINT` | Sí | El mismo endpoint ATS de IoT Core que usa `vigilante-skill`, **sin** `https://` (no se publica) |
| `HISTORY_TABLE` | No | `vigilante_historico` (valor por defecto) |
| `THING_PREFIX` | No | `vigilante-` (valor por defecto) |

### Permisos

Los permisos mínimos están en [`politica-rol.json`](politica-rol.json):

| Acción | Recurso | Para qué |
|---|---|---|
| `dynamodb:Query` | `table/vigilante_historico` | Contar las detecciones de la ventana |
| `iot:UpdateThingShadow` | `thing/vigilante-*` | Escribir el bloqueo en `desired` |

No necesita leer el Shadow ni la tabla de vinculaciones. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`.

**En la cuenta del curso** la función usa el rol `PowerUserRole` (política `PowerUserAccess`), porque esa cuenta no permite crear roles IAM. `politica-rol.json` documenta los permisos mínimos que tendría en un entorno de producción.

## Pruebas

Sin cuenta de AWS ni red: reemplazan los clientes de DynamoDB y de IoT Data por dobles.

```bash
cd lambda-logica && python3 -m pytest tests
```
