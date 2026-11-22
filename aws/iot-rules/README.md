# Reglas de AWS IoT

Las tres reglas están creadas en **AWS IoT Core → Enrutamiento de mensajes → Reglas** (`us-east-2`). Cada archivo `.sql` tiene el SQL exacto que se pega en la consola.

| Regla | Tópico | Lambda | Cuándo se dispara |
|---|---|---|---|
| [`vigilante_lecturas`](vigilante_lecturas.sql) | `$aws/things/+/shadow/update/accepted` | `vigilante-almacenamiento` | Cada `state.reported` aceptado de un Thing `vigilante-*`: eventos y latidos de 60 s. Se guarda como `lectura`. |
| [`vigilante_eventos`](vigilante_eventos.sql) | `$aws/things/+/shadow/update/documents` | `vigilante-almacenamiento` | Cuando cambia `puerta`, cambia `modo` o sube `detecciones`. Se guarda como `cambio`, con el estado anterior y el actual. |
| [`vigilante_deteccion`](vigilante_deteccion.sql) | `$aws/things/+/shadow/update/documents` | `vigilante-logica` | Cuando sube `detecciones` **y** el modo reportado es `automatico`. Es la regla de la Nube (RF13). |

`topic(3)` es el nombre del Thing: el tercer segmento de `$aws/things/<thing>/shadow/...`. El filtro `startswith(topic(3), 'vigilante-')` evita procesar otros Things de la cuenta.

> **Permisos:** las reglas **no tienen rol IAM**, porque su única acción es invocar una Lambda. Al crear la acción, la consola agrega a cada Lambda una política basada en recursos que da `lambda:InvokeFunction` a la entidad principal `iot.amazonaws.com`, limitada al ARN de esa regla.
