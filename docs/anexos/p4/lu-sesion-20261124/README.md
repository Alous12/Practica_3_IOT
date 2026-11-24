# Evidencias reales de la sesión de Lu — 24/11/2026

Thing `vigilante-123456`. Ventana de recepción serie del PC: **18:20:41.968–18:50:41.968 UTC**, equivalente a **14:20:41.968–14:50:41.968 en Bolivia**. Duración: **1800 s**. Captura COM4, 115200 baudios, sin transmitir comandos ni reiniciar el ESP32 desde el capturador. Se inició con `sensor_listo: true` y uptime 386 s.

| Resultado medido | Valor | Alcance |
|---|---:|---|
| Publicaciones con `publish()` exitoso | 132 | Se cuentan líneas `reported ->` de la ventana |
| Lecturas guardadas emparejadas | 132 | Una clave diferente por publicación; 12 atributos coincidentes |
| Integridad observada | 100 % | Esta cohorte con red, no garantía universal |
| Indicios de reinicio / retrocesos de uptime | 0 / 0 | Seguimiento serie, no prueba de ausencia de bloqueos breves |
| Tramo AWS: muestras | 17 | Regla IoT → log `guardado` posterior a `PutItem` |
| Tramo AWS: media / máximo | 160,824 / 378 ms | No mide ESP32 → almacenamiento completo |
| Apagados automáticos Edge observados | 7 | Estado lógico: 29,996–29,998 s, media 29,997 s |
| Latidos observados | 19 intervalos | Recepción serie: 59,995–60,001 s |

## Fuentes conservadas

- `lu-monitor-serie.txt`: captura original del ESP32; las fechas antepuestas son de recepción en el PC.
- `lu-resumen-serial.json`: metadatos originales al terminar la captura. Sus campos `integridad_porcentaje: null` y `pendiente` describen ese momento, antes de recibir el CSV. El resultado posterior está en `lu-resultado-integridad.json`.
- `lu-historico-lecturas-exportado.csv`: exportación de `results (1).csv`, 186 lecturas únicas de DynamoDB, desde 18:14:21.365Z hasta 18:59:51.207Z. Contiene la primera página de 50 filas: no concatenarla de nuevo. No contiene el histórico completo de eventos `alarma#`, `deteccion#`, `puerta#` o `modo#`.
- `lu-cloudwatch-texto-original.txt`: texto aportado del flujo de logs de almacenamiento; incluye copias repetidas de las mismas entradas y mensajes INIT/START/END/REPORT. No se tratan como escrituras adicionales.
- `lu-fuentes-sha256.json`: huellas de los cuatro archivos anteriores para comprobar que las fuentes no cambian.

## Resultados derivados y reproducción

Desde la raíz del repositorio, con Python 3 y sin servicios AWS:

```powershell
python tools/analizar_mediciones_lu.py
```

El script vuelve a generar:

- `lu-publicaciones.csv`: los 132 estados publicados, con hora de recepción del PC.
- `lu-historico-lecturas-sesion.csv`: 132 filas de DynamoDB correspondientes a la cohorte.
- `lu-cruce-publicaciones-historico.csv`: correspondencia uno a uno y diferencias de referencias **que no son latencias**.
- `lu-resultado-integridad.json`: conteos, campos comparados y estado inicial/final.
- `lu-cloudwatch-tramo-almacenamiento.csv` y `lu-cloudwatch-resultado.json`: 17 intervalos AWS. Se eliminan 17 duplicados de copia y se excluyen 2 registros de eventos con resolución temporal distinta.
- `lu-alarmas-serie.csv` y `lu-alarmas-resultado.json`: 19 ciclos completos; 7 apagados Edge y 12 apagados con origen `voz`. Estos últimos no se cuentan como vencimientos del temporizador.
- `lu-latidos-serie.csv` y `lu-latidos-resultado.json`: pares consecutivos con estado igual salvo uptime/RSSI, uptime creciente y sin eventos serie intermedios. No se seleccionan por cumplir un intervalo de tiempo.
- `lu-muestras-dynamodb.csv`: cuatro lecturas completas de la exportación para §5.3.

El cruce normaliza booleanos y el apóstrofo que el CSV añade al RSSI negativo. Compara los **12** atributos de `reported`, preserva estados repetidos y nunca reutiliza una clave. Dos publicaciones con estado idéntico tienen dos filas distintas y cuentan dos veces, una por publicación. Se conservan 54 filas fuera de la cohorte en el CSV original.

## Límites de interpretación

El repositorio revisado estaba en `19a17cd` al preparar la actualización de la rama `lu`. No se leyó una identificación de compilación del binario instalado; los campos P4 presentes no prueban identidad exacta de binario. Las suites anteriores del 24/11 tienen su propia versión y sus propios logs en el directorio superior; no se presentan como nuevos ensayos físicos.

Los timestamps `fecha`/`tipo_ts` de las lecturas proceden de la regla IoT, no del fin de `PutItem`. El log `guardado` se emite después de escribir. No se acreditó alineación entre el reloj de recepción del PC y AWS: algunas fechas AWS preceden al registro serie y **no se presentan como latencias negativas**. LU-05 extremo a extremo sigue sin medición completa.

No se capturó video del servo/sonido, un corte real de WiFi, una prueba de precisión del PIR por distancia, el simulador Alexa P4 ni una activación N-01/N-02 de la Nube. La sesión se mantuvo en modo bloqueo, puerta cerrada, máximo 2 y ventana 10 min; no sustituye el guion N-01 de máximo 3 en modo automático. Las estimaciones están fuera de esta carpeta de resultados y nunca se generan como muestras experimentales.
