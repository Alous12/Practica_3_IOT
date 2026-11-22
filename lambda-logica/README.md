# Lambda de lógica de negocio: `vigilante-logica`

Regla de la Nube (**RF13**). Decide sobre el objeto a partir del histórico, sin intervención del usuario: si en modo automático se acumulan demasiadas detecciones en poco tiempo, pasa el objeto a **bloqueo** y cierra la puerta.

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

1. **Valida el mensaje**: `thingName` = `vigilante-` + 6 dígitos, `ts` entero, `max_detecciones` entre 1 y 20, `ventana_min` entre 1 y 120. Si algo no cuadra, lo registra en el log y termina **sin consultar ni escribir nada**.
2. **Comprueba el modo**: si no es `automatico` no hace nada. La regla SQL ya lo filtra; esto es una doble seguridad.
3. **Cuenta en `vigilante_historico`** las detecciones del mismo Thing, guardadas en modo automático, en los últimos `ventana_min` minutos:
   `thingName = :t AND tipo_ts BETWEEN 'deteccion#<ts − ventana>' AND 'deteccion#<ts − 1 s>'`, con el filtro `modo = automatico`.
   El segundo de la detección actual se excluye porque `vigilante-almacenamiento` la guarda al mismo tiempo. La actual se suma aparte (+1), así nunca se cuenta dos veces.
4. **Decide**: si el total llega a `max_detecciones`, escribe en el Shadow:

   ```json
   {"state": {"desired": {"modo": "bloqueo", "puerta": "cerrada", "origen": "nube"}}}
   ```

   El ESP32 recibe el delta, cierra la puerta, pasa a bloqueo y reporta `"origen": "nube"`. La Lambda actúa sobre el objeto **solo a través de `desired`**: nunca escribe `reported`.

Cada ejecución deja una línea JSON en CloudWatch (`descartado`, `sin_accion` o `bloqueo_activado`) con el conteo, que sirve como evidencia.

## Variables de entorno

| Variable | Valor |
|---|---|
| `IOT_ENDPOINT` | Endpoint ATS de IoT Core, **sin** `https://` (obligatoria; no se publica) |
| `HISTORY_TABLE` | `vigilante_historico` (opcional, es el valor por defecto) |
| `THING_PREFIX` | `vigilante-` (opcional, es el valor por defecto) |

## Permisos (mínimo privilegio)

Política en línea [`politica-rol.json`](politica-rol.json):

| Sid | Acción | Recurso | Para qué |
|---|---|---|---|
| `LeerElHistorico` | `dynamodb:Query` | `table/vigilante_historico` | Contar las detecciones de la ventana |
| `ActuarSoloPorDesired` | `iot:UpdateThingShadow` | `thing/vigilante-*` | Escribir el bloqueo en `state.desired` |

No puede leer el Shadow, escribir en DynamoDB ni tocar otros Things. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`. El permiso para que AWS IoT la invoque (`lambda:InvokeFunction` para `iot.amazonaws.com`) lo agrega la consola al crear la acción de la regla.

## Despliegue

Solo usa la biblioteca estándar y `boto3`, que ya viene en el entorno de Lambda. Por eso **no necesita `.zip` ni dependencias**: se crea la función `vigilante-logica` (Python 3.13), se pega el contenido de `lambda_function.py` en el editor de la consola y se pulsa **Deploy**. Después se configura `IOT_ENDPOINT` y se adjunta la política al rol.

## Pruebas

```bash
cd lambda-logica
python -m pytest -q
```

No acceden a AWS: reemplazan los clientes de DynamoDB y de IoT por dobles. El doble de DynamoDB evalúa la consulta como la tabla real. Hace falta `boto3` y `pytest` instalados, por ejemplo con el entorno de `lambda/` (`lambda/requirements-dev.txt`).
