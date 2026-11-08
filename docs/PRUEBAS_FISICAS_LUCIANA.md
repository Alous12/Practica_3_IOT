## Pruebas físicas pendientes (no realizadas)

| Prueba | Procedimiento y aceptación | Evidencia que debe guardar Luciana |
|---|---|---|
| RF1/RF2 (P06) | Esperar 60 s; pasar frente al PIR, esperar retorno a LOW, repetir. reported refleja los cambios en ≤1 s con red estable. | Monitor serie y Shadow con hora |
| RF3 (P08) | Ordenar abierta y cerrada; comprobar movimiento y reported. | Video del pestillo y Shadow |
| Estabilidad (P11) | 30 min sin reinicios; comando cada 5 min. uptime_s crece y alcanza ≥1800; anotar rssi. | Capturas inicio, intermedias y final |
| Detección (P12) | 20 intentos independientes por distancia a 1, 2, 3 y 4 m. Objetivo ≥95% hasta 3 m; 10 min sin presencia, cero falsos positivos. | Tabla de conteos y distancias |
| Reportes (P14) | Medir latidos a 60 s ±1 s sin eventos y evento ≤1 s. | Marcas de tiempo MQTT/serie |
| Reconexión (P15) | Puerta cerrada, cortar WiFi 60 s; ordenar abierta durante el corte. Restaurar y verificar reconexión ≤30 s y apertura sin nueva orden. | Video, monitor y desired=reported |

No deducir resultados físicos de una compilación o una prueba simulada.
La reconexión es una prueba de integración con la capa net/ de Alejandro.
El estado puerta es estimado por software: no existe sensor del pestillo.

### Registro de estabilidad para completar con datos reales

| Minuto | uptime_s | rssi (dBm) | Reinicios | Comando/observación | Evidencia |
|---|---|---|---|---|---|
| 0 | pendiente | pendiente | pendiente | inicio | pendiente |
| 5 | pendiente | pendiente | pendiente | | pendiente |
| 10 | pendiente | pendiente | pendiente | | pendiente |
| 15 | pendiente | pendiente | pendiente | | pendiente |
| 20 | pendiente | pendiente | pendiente | | pendiente |
| 25 | pendiente | pendiente | pendiente | | pendiente |
| 30 | pendiente | pendiente | pendiente | final | pendiente |

