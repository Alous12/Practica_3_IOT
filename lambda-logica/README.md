# Lambda `vigilante-logica`: lógica de negocio en la nube (RF13)

Responsable: Rubén.

Regla de la Nube (**RF13**). Decide sobre el objeto a partir del histórico, sin intervención del usuario: si en modo automático se acumulan demasiadas detecciones en poco tiempo, pasa el objeto a **bloqueo**, cierra la puerta y enciende la alarma. Actúa sobre el ESP32 **solo a través de `state.desired`** del Device Shadow: nunca le habla directamente.

Esta carpeta deja documentado **lo que está desplegado** en AWS (región `us-east-2`).

| Archivo | Qué es | Dónde se usa en AWS |
|---|---|---|
| [`lambda_function.py`](lambda_function.py) | Código de la función (`Handler: lambda_function.lambda_handler`, Python 3.13) | Lambda → `vigilante-logica` → pestaña *Code* |
| [`politica-rol.json`](politica-rol.json) | Política en línea del rol de ejecución de `vigilante-logica` | IAM → Roles → rol de `vigilante-logica` |
| [`events/`](events/) | Mensajes de ejemplo de la regla (automático y manual) | Lambda → pestaña *Test* |
| [`tests/test_logica.py`](tests/test_logica.py) | Pruebas con pytest, sin acceso a AWS | Local |

## Cuándo se ejecuta

La invoca la regla de AWS IoT [`vigilante_deteccion`](../aws/iot-rules/vigilante_deteccion.sql) cada vez que el Shadow de un Thing `vigilante-*` registra una **detección nueva** (`detecciones` sube) **en modo `automatico`**. El mensaje que recibe es:

```json
{"thingName": "vigilante-482917", "ts": 1795169742, "detecciones": 4,
 "modo": "automatico", "max_detecciones": 3, "ventana_min": 10}
```

`ts` es el instante de la detección (epoch en segundos, tomado de la metadata del Shadow). `max_detecciones` y `ventana_min` son los parámetros que el usuario configuró por voz y que el ESP32 reporta.

## Qué hace

1. **Valida el mensaje**: `thingName` = `vigilante-` + 6 dígitos, `ts` entero positivo, `max_detecciones` entre 1 y 20, `ventana_min` entre 1 y 120. Si algo falta o no cuadra, lo registra en el log y termina (`"accion": "ninguna"`) **sin consultar ni escribir nada**.
2. **Comprueba el modo**: si no es `automatico` no hace nada. La regla SQL ya lo filtra; esto es una doble seguridad.
3. **Cuenta en `vigilante_historico`** las detecciones del mismo Thing, guardadas en modo automático, en los últimos `ventana_min` minutos. Hace un `Query` (nunca `Scan`):
   `thingName = :t AND tipo_ts BETWEEN 'deteccion#<ts − ventana>' AND 'deteccion#<ts − 1 s>'`, con el filtro `modo = automatico`, pide solo el conteo (`Select: COUNT`) y sigue `LastEvaluatedKey` si la respuesta viene paginada. Al resultado le suma 1, que es la detección actual.
4. **Decide**: si el total llega a `max_detecciones`, escribe en el Shadow:

   ```json
   {"state": {"desired": {"modo": "bloqueo", "puerta": "cerrada", "alarma": "encendida", "origen": "nube"}}}
   ```

   El ESP32 recibe el delta, pasa a bloqueo, cierra la puerta, enciende la alarma y reporta `"origen": "nube"`. La Lambda actúa sobre el objeto **solo a través de `desired`**: nunca escribe `reported`.

Cada ejecución deja una línea JSON en CloudWatch (`descartado`, `sin_accion` o `bloqueo_activado`) con el conteo, que sirve como evidencia.

### Por qué la consulta termina en `ts − 1`

La Lambda de almacenamiento guarda la detección actual en `vigilante_historico` **al mismo tiempo** que se invoca esta Lambda. Según qué termine primero, esa fila puede estar o no en la tabla al momento de la consulta. Para no contarla dos veces (ni olvidarla), la consulta llega solo hasta el segundo anterior (`ts − 1`) y la detección actual se suma siempre aparte con `+1`.

## Configuración en AWS

| Dato | Valor |
|---|---|
| Nombre | `vigilante-logica` (Python 3.13), handler `lambda_function.lambda_handler` |
| Disparador | Regla de IoT `vigilante_deteccion` |
| Tiempo de espera | 10 s |
| Logs | CloudWatch `/aws/lambda/vigilante-logica`, retención de 1 semana |

### Variables de entorno

| Variable | Obligatoria | Valor |
|---|---|---|
| `IOT_ENDPOINT` | Sí | El mismo endpoint ATS de IoT Core que usa `vigilante-skill`, **sin** `https://` (no se publica) |
| `HISTORY_TABLE` | No | `vigilante_historico` (valor por defecto) |
| `THING_PREFIX` | No | `vigilante-` (valor por defecto) |

### Permisos (mínimo privilegio)

Política en línea [`politica-rol.json`](politica-rol.json):

| Sid | Acción | Recurso | Para qué |
|---|---|---|---|
| `LeerElHistorico` | `dynamodb:Query` | `table/vigilante_historico` | Contar las detecciones de la ventana |
| `ActuarSoloPorDesired` | `iot:UpdateThingShadow` | `thing/vigilante-*` | Escribir el bloqueo en `state.desired` |

No puede leer el Shadow, escribir en DynamoDB ni tocar otros Things. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`. El permiso para que AWS IoT la invoque (`lambda:InvokeFunction` para `iot.amazonaws.com`) lo agrega la consola al crear la acción de la regla.

**En la cuenta del curso** la función usa el rol `PowerUserRole` (política `PowerUserAccess`), porque esa cuenta no permite crear roles IAM. `politica-rol.json` documenta los permisos mínimos que tendría en un entorno de producción.

## Despliegue

Solo usa la biblioteca estándar y `boto3`, que ya viene en el entorno de Lambda. Por eso **no necesita `.zip` ni dependencias**: se crea la función `vigilante-logica` (Python 3.13), se pega el contenido de `lambda_function.py` en el editor de la consola y se pulsa **Deploy**. Después se configura `IOT_ENDPOINT` y se adjunta la política al rol.

## Pruebas

```bash
cd lambda-logica
python -m pytest -q
```

No acceden a AWS: reemplazan los clientes de DynamoDB y de IoT por dobles. El doble de DynamoDB evalúa la consulta como la tabla real. Hace falta `boto3` y `pytest` instalados, por ejemplo con el entorno de `lambda/` (`lambda/requirements-dev.txt`).
