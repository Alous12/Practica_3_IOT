-- Regla:   vigilante_eventos
-- Acción:  Lambda vigilante-almacenamiento
-- Para qué: guardar en vigilante_historico los cambios de estado (tipo "cambio"): apertura o
--           cierre de la puerta, cambio de modo, encendido o apagado de la alarma y cada
--           detección nueva, con el estado anterior y el actual para conocer el origen del cambio.
--           ts = instante en que el Shadow registró detecciones (metadata, epoch en segundos).
SELECT 'cambio' AS tipo, topic(3) AS thingName,
       current.metadata.reported.detecciones.timestamp AS ts,
       previous.state.reported AS anterior, current.state.reported AS actual
FROM '$aws/things/+/shadow/update/documents'
WHERE startswith(topic(3), 'vigilante-')
  AND (current.state.reported.puerta <> previous.state.reported.puerta
       OR current.state.reported.modo <> previous.state.reported.modo
       OR current.state.reported.alarma <> previous.state.reported.alarma
       OR current.state.reported.detecciones > previous.state.reported.detecciones)
