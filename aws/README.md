# Configuraciones exportadas de AWS

Todos los recursos se crean en **us-east-2 (Ohio)**. Reemplace `<ACCOUNT_ID>` por el ID de 12 dígitos de su cuenta (menú de su usuario, arriba a la derecha de la consola).

| Archivo | Dónde se usa | Contenido |
|---|---|---|
| `iot-policy.json` | AWS IoT Core > Administrar > Seguridad > Políticas > `vigilante-device-policy` | Política del certificado del objeto inteligente. Usa la variable `${iot:Connection.Thing.ThingName}`: cada dispositivo solo puede conectarse con un client ID igual a su nombre de Thing y solo publica, se suscribe y recibe en los tópicos de **su propio** Shadow (`$aws/things/<su-thing>/shadow/*`: update, get, delete y sus accepted/rejected/delta/documents). No puede tocar el Shadow de otro Thing ni ningún otro tópico. Sirve para todos los Things `vigilante-*` sin modificarla, y permite las pruebas de clase con MQTT.fx/MQTTX usando el mismo certificado. |
| `lambda-role-policy.json` | IAM > Roles > `vigilante-lambda-role` > política en línea `vigilante-lambda-minimo` | Mínimo privilegio para la Lambda: `iot:GetThingShadow`, `iot:UpdateThingShadow`, `iot:DescribeThing` sobre `thing/vigilante-*` y `dynamodb:GetItem/PutItem/DeleteItem` sobre la tabla de vinculaciones. Los logs los da la política administrada `AWSLambdaBasicExecutionRole`. |
| `dynamodb-table.json` | DynamoDB > Tables | Definición de la tabla `vigilante_vinculaciones` (clave de partición `userId`, modo de capacidad bajo demanda (`PAY_PER_REQUEST`), la configuración predeterminada de la consola; con el uso de la práctica el costo es de fracciones de centavo y lo cubren los créditos del plan gratuito). Equivale a `aws dynamodb create-table --cli-input-json file://dynamodb-table.json`. |

## Permisos asignados y por qué

- **No se usan access keys** en ningún código. El ESP32 se autentica con su certificado X.509 (TLS mutuo) y la Lambda con las credenciales temporales de su rol de ejecución.
- Si para simplificar usaron políticas amplias (`AWSIoTDataAccess`, `AmazonDynamoDBFullAccess` o `"Resource": "*"`), documéntenlo en el informe e indiquen que los archivos de esta carpeta son los permisos mínimos para producción.
