-- Regla:   vigilante_lecturas
-- Acción:  Lambda vigilante-almacenamiento
-- Para qué: guardar en vigilante_historico cada reporte aceptado del Shadow (tipo "lectura").
--           Se dispara con cada state.reported que AWS IoT acepta (eventos y latidos de 60 s).
--           ts = timestamp() de la regla, en milisegundos.
SELECT 'lectura' AS tipo, topic(3) AS thingName, timestamp() AS ts, state.reported AS reported
FROM '$aws/things/+/shadow/update/accepted'
WHERE startswith(topic(3), 'vigilante-') AND NOT isUndefined(state.reported)
