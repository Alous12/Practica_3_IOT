# Lambda de lógica: `vigilante-skill`

Responsable: Rubén.

Es la función Lambda que atiende la skill de Alexa (*backend*): resuelve el Thing de cada usuario en DynamoDB y lee o escribe su Device Shadow. Esta carpeta deja documentado **lo que está desplegado** en AWS, junto a las otras Lambdas del proyecto (por ejemplo `lambda-almacenamiento/`).

| Archivo | Qué es | Dónde se usa en AWS |
|---|---|---|
| [`lambda_function.py`](lambda_function.py) | Punto de entrada (`Handler: lambda_function.lambda_handler`) | Raíz del `.zip` de la función `vigilante-skill` |
| [`politica-rol.json`](politica-rol.json) | Política en línea `vigilante-lambda-minimo` del rol `vigilante-lambda-role` | IAM → Roles → `vigilante-lambda-role` |

## El código fuente vive en `lambda/`

`lambda_function.py` importa el paquete [`lambda/vigilante/`](../lambda/vigilante/) (configuración, manejadores, gateway del Shadow, repositorio de DynamoDB y frases). Por eso el `.zip` **no** se arma desde esta carpeta, sino con:

```bash
cd lambda && ./build.sh          # Linux / macOS
cd lambda; .\build.ps1           # Windows
```

El resultado es `lambda/build/lambda_deployment.zip` (no se sube a Git), que se carga en la consola de Lambda.

Para que esta copia no quede desactualizada, la prueba `test_lambda_logica_coincide_con_lo_que_se_despliega` (en `lambda/tests/test_contratos.py`) exige que los dos archivos sean idénticos a [`lambda/lambda_function.py`](../lambda/lambda_function.py) y a [`aws/lambda-role-policy.json`](../aws/lambda-role-policy.json).

## Permisos (mínimo privilegio)

| Acción | Recurso | Para qué |
|---|---|---|
| `iot:DescribeThing` | `thing/vigilante-*` | Validar que el Thing exista antes de vincularlo |
| `iot:GetThingShadow` | `thing/vigilante-*` | Leer `reported`: movimiento, puerta, modo, parámetros y origen |
| `iot:UpdateThingShadow` | `thing/vigilante-*` | Escribir `desired`: puerta, modo, `max_detecciones` y `ventana_min`, siempre con `"origen": "voz"` |
| `dynamodb:GetItem` / `PutItem` / `DeleteItem` | `table/vigilante_vinculaciones` | Resolver, crear o cambiar, y borrar la vinculación |

La ampliación (modo y parámetros) **no necesita permisos nuevos**: son atributos más del mismo Shadow. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`.

## Variables de entorno

| Variable | Valor |
|---|---|
| `IOT_ENDPOINT` | Endpoint ATS de IoT Core (obligatoria; no se publica) |
| `LINKS_TABLE` | `vigilante_vinculaciones` |
| `CONFIRM_TIMEOUT_S` | 3 (opcional): segundos que se espera la confirmación del ESP32 |
| `STALE_AFTER_S` | 150 (opcional): segundos sin reporte para avisar "puede estar desconectado" |
