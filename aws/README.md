# Configuraciones exportadas de AWS

Todos los recursos se crean en **us-east-2 (Ohio)**. Reemplace `<ACCOUNT_ID>` por el ID de 12 dígitos de su cuenta (menú de su usuario, arriba a la derecha de la consola).

| Archivo | Dónde se usa | Contenido |
|---|---|---|
| `iot-policy.json` | AWS IoT Core > Administrar > Seguridad > Políticas > `vigilante-device-policy` | Política del certificado del objeto inteligente. Usa la variable `${iot:Connection.Thing.ThingName}`: cada dispositivo solo puede conectarse con un client ID igual a su nombre de Thing y solo publica, se suscribe y recibe en los tópicos de **su propio** Shadow (`$aws/things/<su-thing>/shadow/*`: update, get, delete y sus accepted/rejected/delta/documents). No puede tocar el Shadow de otro Thing ni ningún otro tópico. Sirve para todos los Things `vigilante-*` sin modificarla, y permite las pruebas de clase con MQTT.fx/MQTTX usando el mismo certificado. |
| `lambda-role-policy.json` | IAM > Roles > `vigilante-lambda-role` > política en línea `vigilante-lambda-minimo` | Mínimo privilegio para la Lambda: `iot:GetThingShadow`, `iot:UpdateThingShadow`, `iot:DescribeThing` sobre `thing/vigilante-*` y `dynamodb:GetItem/PutItem/DeleteItem` sobre la tabla de vinculaciones. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`. |
| `dynamodb-table.json` | DynamoDB > Tables | Definición de la tabla `vigilante_vinculaciones` (clave de partición `userId`, modo de capacidad bajo demanda (`PAY_PER_REQUEST`), la configuración predeterminada de la consola; con el uso de la práctica el costo es de fracciones de centavo y lo cubren los créditos del plan gratuito). Equivale a `aws dynamodb create-table --cli-input-json file://dynamodb-table.json`. |
| `dynamodb-historico.json` | DynamoDB > Tables | Definición de la tabla de histórico `vigilante_historico`: clave de partición `thingName` (S) y de ordenación `tipo_ts` (S) con formato `<tipo>#<fecha ISO UTC>` (`lectura`, `deteccion`, `puerta` o `modo`), bajo demanda (`PAY_PER_REQUEST`) y etiqueta `proyecto=vigilante-inteligente`. Equivale a `aws dynamodb create-table --cli-input-json file://dynamodb-historico.json`. |
| `dynamodb-historico-ttl.json` | DynamoDB > Tables > `vigilante_historico` > Configuración adicional > Tiempo de vida (TTL) | Activa el TTL en el atributo `expira` (epoch en segundos): DynamoDB borra solo los registros vencidos (30 días por defecto, variable `TTL_DAYS` de `vigilante-almacenamiento`). Equivale a `aws dynamodb update-time-to-live --cli-input-json file://dynamodb-historico-ttl.json`. |
| [`iot-rules/`](iot-rules/) | AWS IoT Core > Enrutamiento de mensajes > Reglas | SQL exacto de las tres reglas: `vigilante_lecturas` y `vigilante_eventos` (→ `vigilante-almacenamiento`) y `vigilante_deteccion` (→ `vigilante-logica`). Ver su [README](iot-rules/README.md). |
| `almacenamiento-role-policy.json` | IAM > Roles > rol de `vigilante-almacenamiento` > política en línea | Mínimo privilegio para la Lambda de almacenamiento: solo `dynamodb:PutItem` sobre `table/vigilante_historico`. No lee el histórico ni toca el Shadow. |
| [`../lambda-logica/politica-rol.json`](../lambda-logica/politica-rol.json) | IAM > Roles > rol de `vigilante-logica` > política en línea | Mínimo privilegio para la regla de la Nube: `dynamodb:Query` sobre `table/vigilante_historico` e `iot:UpdateThingShadow` sobre `thing/vigilante-*` (actúa solo por `desired`). |

## Patrones de acceso de `vigilante_historico`

Todas las consultas son `Query` sobre la clave primaria (sin `Scan` ni índices secundarios): la partición es el Thing y el prefijo de `tipo_ts` separa los tipos de registro, que se ordenan por fecha.

| Pregunta | Condición de clave (`thingName = t AND …`) | Filtro | Quién la usa |
|---|---|---|---|
| Lecturas de un Thing entre dos fechas | `tipo_ts BETWEEN 'lectura#<desde>' AND 'lectura#<hasta>'` | — | Consulta del histórico (informe, gráficas) |
| Detecciones en automático de la última ventana | `tipo_ts BETWEEN 'deteccion#<ts − ventana>' AND 'deteccion#<ts − 1 s>'` | `modo = automatico` | `vigilante-logica` (RF13) |
| Aperturas y cierres de un día, con su origen | `begins_with(tipo_ts, 'puerta#2026-11-20')` | — | Consulta del histórico (quién abrió: voz, edge o nube) |
| Historial de cambios de modo | `begins_with(tipo_ts, 'modo#')` | — | Consulta del histórico |

## Permisos asignados y por qué

- **No se usan access keys** en ningún código. El ESP32 se autentica con su certificado X.509 (TLS mutuo) y la Lambda con las credenciales temporales de su rol de ejecución.
- Si para simplificar usaron políticas amplias (`AWSIoTDataAccess`, `AmazonDynamoDBFullAccess` o `"Resource": "*"`), documéntenlo en el informe e indiquen que los archivos de esta carpeta son los permisos mínimos para producción.
