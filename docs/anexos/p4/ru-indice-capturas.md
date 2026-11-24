# Capturas reales aportadas — AWS y Alexa, P4

Recibidas el 24/11/2026. Las imágenes se conservan sin alterar su contenido; las huellas SHA-256 están en [ru-capturas-fuentes.json](ru-capturas-fuentes.json).

Se recibieron **12 imágenes**, que cubren **6 de las 7 evidencias solicitadas**. La séptima, Shadow del bloqueo confirmado en `reported`, sigue incompleta: la captura recibida muestra `desired`. Los logs de decisión no aportan por sí solos el tiempo hasta el efecto en el objeto.

| Evidencia | Archivo recibido | Qué demuestra y límites |
|---|---|---|
| Intents P4 | [Parte 1](ru-alexa-intents-p4.png), [parte 2](ru-alexa-intents-p4-02.png), [parte 3](ru-alexa-intents-p4-03.png) | Las tres partes cubren 20 intents, incluidos los integrados y los de modo, parámetros y alarma. La tercera indica `1–20 of 20 Intents`. Los recortes no muestran el nombre/idioma de la skill |
| Compilación | [ru-alexa-build-p4.png](ru-alexa-build-p4.png) | Build History: `Latest (10)`, compilación exitosa 24/11/2026 a las 16:59, idioma `Spanish (MX) + 1`. La segunda lengua no se identifica en el recorte; no se afirma que sea es-US ni se acredita identidad exacta con el JSON versionado |
| Reglas activas | [reglas-iot.png](reglas-iot.png) | vigilante_lecturas, vigilante_eventos y vigilante_deteccion aparecen Activo. No muestra el SQL ni las acciones completas y no sustituye P-A3 funcional |
| TTL | [historico-ttl.png](historico-ttl.png) | Se ve vigilante_historico, estado Activada y atributo expira. La fecha de actualización visible es 24/11/2026 17:10 UTC-4; no es necesariamente la fecha de activación |
| Decisión positiva Nube | [ru-cw-bloqueo.png](ru-cw-bloqueo.png) | Log 24/11/2026 20:30:00.300 UTC, vigilante-123456, 3 detecciones, umbral 3, ventana 10 min. desired: bloqueo, puerta cerrada, alarma encendida, origen nube. Acredita la decisión de la Lambda; no su aplicación ni la latencia N-01 |
| Decisión negativa Nube | [ru-cw-sin-accion.png](ru-cw-sin-accion.png) | Log 24/11/2026 20:29:40.030 UTC, mismo Thing, 2 detecciones, umbral 3, ventana 10 min y sin_accion. Acredita que esa invocación no ordenó el bloqueo; no mide el estado físico del buzzer |
| Shadow, orden solicitada | [ru-shadow-bloqueo-desired.png](ru-shadow-bloqueo-desired.png) | desired tiene modo bloqueo, puerta cerrada, alarma encendida, origen nube, umbral 3 y ventana 1. reported está recortado y no permite verificar aplicación. No se atribuye esta imagen al mismo ensayo de ventana 10 min de los logs anteriores |

## Antecedentes y recortes adicionales

| Archivo | Alcance |
|---|---|
| [historico-ttl-detalle.png](antecedentes/historico-ttl-detalle.png) | Primer recorte de TTL activado en expira; no muestra la tabla. La versión amplia de arriba es la evidencia principal |
| [ru-cw-bloqueo-anterior-sin-alarma.png](antecedentes/ru-cw-bloqueo-anterior-sin-alarma.png) | Log del 22/11/2026: bloqueo sin alarma en desired. Es antecedente histórico; no prueba la orden con alarma del P4 actual |
| [ru-shadow-manual-previo.png](antecedentes/ru-shadow-manual-previo.png) | Estado previo del Thing en manual. No se presenta como bloqueo aplicado por la Nube |

## Evidencias de la sesión final (24/11/2026)

| Archivo | Alcance |
|---|---|
| [ru-shadow-bloqueo.png](ru-shadow-bloqueo.png) | Shadow con `desired` de la Nube (bloqueo, alarma encendida, origen nube). La consola no refresca sola: el `reported` visible es el previo |
| [ru-monitor-serie-20261124.txt](ru-monitor-serie-20261124.txt) | Monitor serie con hora en ms (endpoint tapado). Confirma la aplicación: `reported` con `bloqueo`, `alarma: encendida` y `origen: nube` 32 ms después del `delta`, y da los tiempos de N-01 (3 ensayos, máx. 0,603 s), LU-06, LU-07 y LU-08 |
| `ru-sim-01-modo.png` … `ru-sim-13-manual.png`, `ru-sim-previo-11-abrir.png` | Guion S-01 a S-13 en el simulador, con Skill ID y `userId` tapados (INFORME_P4 §4.6) |

Con el monitor serie queda confirmada la aplicación del bloqueo en `reported`, que esta captura del Shadow no muestra por sí sola.
