-- Regla:   vigilante_deteccion
-- Acción:  Lambda vigilante-logica
-- Para qué: regla de la Nube (RF13). Avisa a vigilante-logica de cada detección nueva en modo
--           automático, con los parámetros configurados (max_detecciones y ventana_min), para
--           que decida si pasa el objeto a bloqueo.
--           ts = instante en que el Shadow registró detecciones (metadata, epoch en segundos).
SELECT topic(3) AS thingName,
       current.metadata.reported.detecciones.timestamp AS ts,
       current.state.reported.detecciones AS detecciones,
       current.state.reported.modo AS modo,
       current.state.reported.max_detecciones AS max_detecciones,
       current.state.reported.ventana_min AS ventana_min
FROM '$aws/things/+/shadow/update/documents'
WHERE startswith(topic(3), 'vigilante-')
  AND current.state.reported.modo = 'automatico'
  AND current.state.reported.detecciones > previous.state.reported.detecciones
