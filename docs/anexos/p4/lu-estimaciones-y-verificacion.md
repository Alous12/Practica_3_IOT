# Estimaciones de pruebas pendientes y verificación

Actualizado el 24/11/2026 por Luciana. Este anexo acompaña la versión final del informe y separa los resultados observados, las estimaciones para pruebas no ejecutadas y las verificaciones pendientes de despliegue.

**M** = dato observado con fuente conservada. **E** = escenario orientativo solicitado para campos sin medición. **Código** = comportamiento previsto y probado con dobles; no es despliegue verificado. Una E no permite aprobar un RNF, no es un intervalo estadístico y no crea un promedio/máximo experimental. No se fabrican capturas, logs, CSV de ensayos ni resultados individuales.

## Lo que ya tiene evidencia real

| Prueba | Resultado M | Evidencia |
|---|---|---|
| P-A1, parte de estabilidad | Captura continua 1800 s; 132 publicaciones; sin indicios de reinicio/retroceso de uptime | [Log](lu-monitor-serie.txt), [resumen calculado](lu-resumen-serial.json) |
| LU-04 | 132 lecturas guardadas / 132 publicaciones, 100 % observado | [Exportación 186 filas](lu-historico-lecturas-exportado.csv), [cruce 132 filas](lu-cruce-publicaciones-historico.csv) |
| LU-05, tramo AWS | 17 intervalos; media 160,824 ms; máximo 378 ms | [Muestras](lu-cloudwatch-tramo-almacenamiento.csv) |
| LU-07, apagado Edge lógico | 7 ciclos, media 29,997 s; mínimo 29,996 y máximo 29,998 s | [Todos los ciclos](lu-alarmas-serie.csv) |
| G-01, latidos | 19 intervalos de 59,995–60,001 s | [Intervalos](lu-latidos-serie.csv) |
| §5.3 | Cuatro muestras completas; 132 lecturas de cohorte | [Muestras](lu-muestras-dynamodb.csv) |

La observación serie del temporizador y del latido tiene resolución de recepción del PC; no es un cronómetro del sonido o del movimiento. Se conservan el [registro serie](lu-monitor-serie.txt), el [texto original de CloudWatch](lu-cloudwatch-texto-original.txt) y los archivos de cálculo citados en la tabla.

## Escenarios E utilizados en el informe

| Prueba | Escenario E orientativo, no medido | Fundamento y supuestos | Ensayo necesario para obtener M |
|---|---|---|---|
| P-A1 completo | El registro apoya estabilidad, pero no permite estimar falsos positivos o respuesta mecánica | Se observó continuidad y actividad lógica, sin pasadas controladas | Ejecutar el guion físico completo; anotar pilas, montaje, respuesta y sonido |
| LU-05 extremo a extremo | **0,2–1,9 s** en red estable | Sumar al tramo AWS observado de 0,111–0,378 s un supuesto de transporte de 0,1–1,5 s; redondeo de escenario. Se desconoce el transporte real | Diez emisiones con hora UTC de inicio acreditada y log posterior a escritura correspondiente; medir máximo |
| N-01 | **0,4–5,5 s** detección → bloqueo en un escenario normal | Presupuesto supuesto: reporte/red 0,1–1,5 s + evaluación/consulta/ejecución 0,2–2 s + delta/aplicación 0,1–2 s. No está calibrado con vigilante-logica | Cinco ensayos en automático, umbral 3 y ventana 1 min; esperar 70 s entre ensayos según §4.7 y restaurar ventana 10 al terminar; conservar logs de CloudWatch y Shadow con origen nube |
| N-02 | Resultado esperado **sin_accion**; decisión **0,3–2 s** | Dos detecciones y umbral 3; comportamiento probado con dobles. El tiempo es supuesto | Ensayo integrado, log real con conteo 2 y prueba de ausencia de bloqueo |
| S-01, S-05, S-07, S-09, S-12 | **0,3–2 s** | Consultas o rechazo de rango; presupuesto de ida/vuelta y backend, sin activación física. Cold start/red pueden excederlo | Capturar cada paso con JSON de entrada/salida y medir desde envío |
| S-02/03/04/06/08/10/11/13 | **0,8–4 s** | Presupuesto general de diálogo y, cuando corresponda, modificación/confirmación. S-03 es un rechazo; se conserva un escenario amplio, no una comparación de rendimiento | Capturas reales y medida de cada paso; S-11/S-13 con condiciones iniciales correctas |
| V-01 puerta y alarma | **0,8–4 s** | Escenario de voz/simulador + Lambda + Shadow. Puede superar el RNF de 3 s, por lo que no se da por cumplido | Diez órdenes de cada actuador y logs de confirmación. No empezar a contar después de la respuesta |
| LU-06 | Reacción lógica **0,05–0,5 s** sin bloqueos | Filtro PIR de 50 ms y evaluación local. El desplazamiento mecánico, la acústica y TLS/MQTT pueden añadir tiempo | Diez mediciones por efecto con las marcas de tiempo del monitor serie; condición inicial puerta abierta; medir hasta movimiento/primer pitido |
| LU-07 voz/Nube | Aproximadamente **30 s** si no se apaga antes por orden | `ALARM_MAX_MS`, sin renovación del plazo mientras ya está encendida; no mide la respuesta física | Encendidos por cada origen y su apagado real; comparar duración y origen |
| LU-08 offline | Cierre/alarma locales y apagado cercano a **30 s** | Las reglas se evalúan antes de la comprobación de red; pruebas con transporte simulado | Ensayo con hotspot apagado; conservar monitor serie, reconexión y Shadow final |
| G-01 evento | **0,05–1 s** en red estable | Filtro, publicación por cambio y transporte supuesto; confirmaciones tienen prioridad | Hora del evento y recepción MQTT sincronizadas; los latidos medidos no prueban este retardo |
| G-02 reconexión | **5–30 s** tras restaurar una red estable | Escenario supuesto con reintentos de conexión; no deducido de un corte de esta sesión | Tres cortes de 60 s; anotar restauración, conexión, sincronización y orden pendiente |
| G-03 precisión | Referencia **98,3 % y 0 falsos positivos**, solo si se reproduce P3 | Antecedente de P3 con el mismo sensor; el buzzer y montaje cambian, por eso no se adopta como resultado P4 | 20 pasadas a 1/2/3 m y 10 min sin presencia; sin denominador controlado no se estima precisión nueva |

Los intervalos E son supuestos de planificación y pueden excederse. No se obtienen n muestras repitiendo un mismo escenario n veces. Los resultados de latencia y precisión que se defenderán como medidos deben proceder de los ensayos indicados.

## Capturas por obtener

| Sección | Ya adjunto | Por capturar |
|---|---|---|
| §3.2.1 | [Lecturas](lu-historico-lecturas-real.png), [eventos de alarma](lu-historico-alarmas-real.png), CSV de lecturas | Las tres reglas activas, SQL de eventos, claves/capacidad de tabla, TTL **habilitado** y atributo, Shadow P4, otros tipos de evento |
| §3.3 | Modelo JSON versionado con 20 intents; pruebas automáticas previas | Lista real de los 20 intents y compilación correcta del modelo vigente |
| §4.7 | Ningún log de bloqueo real conservado en esta sesión | CloudWatch `bloqueo_activado` y `sin_accion` de vigilante-logica y Shadow con origen nube |
| S-01 a S-13 | Respuestas esperadas y pruebas con dobles | Trece capturas con JSON Input/Output y las condiciones del guion |
| LU-05 | Texto original y tabla de 17 intervalos AWS | Emisiones UTC sincronizadas para el tramo completo |

Una imagen con el atributo `expira` no confirma que TTL esté activo. Un JSON versionado no confirma que Alexa lo haya compilado. Un campo de firmware P4 no prueba identidad de binario. No se generan imágenes que aparenten ser capturas de consola.

## Verificacion del despliegue

Se intentó abrir la consola el 24/11/2026, pero la herramienta detuvo el acceso porque no pudo determinar la URL del navegador con suficiente confianza. **No se accedió ni se alteró el despliegue.** Los siguientes son pasos de verificación, no afirmaciones sobre la cuenta.

| Elemento | Estado comprobable en el repositorio | Cómo comprobarlo en la consola / equipo |
|---|---|---|
| SQL de `vigilante_eventos` | `aws/iot-rules/vigilante_eventos.sql` incluye cambios de alarma | AWS IoT Core → Enrutamiento de mensajes → Reglas → vigilante_eventos → revisar SQL y acción. Comparar texto/versionado, incluyendo `alarma`; capturar |
| LOCKDOWN | `lambda-logica/lambda_function.py` declara modo bloqueo, puerta cerrada, **alarma encendida**, origen nube | Lambda → vigilante-logica → Código → buscar `LOCKDOWN`, comparar el diccionario completo y confirmar implementación actual. No basta buscar la palabra |
| Paquete de `vigilante-skill` | Fuentes en `lambda/`; los ZIP no se versionan | Lambda → vigilante-skill → Código/descarga del paquete desplegado. Comparar archivos con los de `lambda/` sin publicar secretos; revisar última modificación y pruebas del guion P4 |
| Modelo Alexa | `alexa/interaction-model.es-US.json`: 20 intents y TipoModo | Alexa Developer Console → skill → Build → Interaction Model/JSON Editor → comparar modelo e idioma; revisar compilación sin errores y capturar |
| Firmware instalado | Se observan campos P4 y comportamiento lógico; no se leyó ID de compilación | Revisar entorno `esp32dev-aws` y compilación subida. Para identidad exacta usar identificación de versión/hash o una carga documentada; no afirmar identidad solo por los campos |
| Arquitectura de la skill | No se asume a partir del código Python ni del plan gratuito | Lambda → vigilante-skill → **Código → Runtime settings / Configuración del tiempo de ejecución** → leer **Architecture/Arquitectura**, x86_64 o arm64. Guardar evidencia; no cambiarla para la prueba |
| TTL | JSON previsto en `aws/dynamodb-historico-ttl.json`; ítems con 30 días de diferencia | DynamoDB → vigilante_historico → configuración de TTL → comprobar habilitado en `expira`, no solo presencia de columna |
| Shadow | Estado previsto y reportes de la sesión | IoT Core → Things → vigilante-123456 → Shadow clásico: reported con puerta/alarma/modo/parámetros/origen; guardar JSON sin certificados ni endpoint |

Conservar las capturas originales y ocultar identificadores de cuenta/Skill ID antes de incorporarlas al informe. La verificación de permisos, SQL, ZIP o compilación nunca se completa con una estimación.

La ubicación de la arquitectura corresponde a [AWS Lambda: configuración de arquitectura](https://docs.aws.amazon.com/lambda/latest/dg/foundation-arch.html). La activación de TTL es una configuración de la tabla independiente del contenido del ítem: [AWS DynamoDB: habilitar TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-how-to.html). Documentación consultada el 24/11/2026; estas referencias no verifican la cuenta del equipo.

## Pruebas recomendadas para completar la validación

1. Revisar lo ya medido en el informe y mantener el vínculo al CSV y al log.
2. Priorizar un ensayo Edge/offline y las capturas de configuración: aportan evidencia que el histórico de lecturas no puede dar.
3. Ejecutar N-01/N-02 y el guion P4 de Alexa con tiempos y condiciones iniciales correctas.
4. Completar LU-05 con un inicio acreditado, V-01 y G-02/G-03. Exportar los eventos para conteos por día/origen.
5. Si se ejecutan estos ensayos, sustituir cada E por sus resultados M y calcular promedio y máximo únicamente sobre muestras reales. En esta versión final, los RNF sin medición permanecen identificados como pendientes de validar; las estimaciones no los aprueban.
