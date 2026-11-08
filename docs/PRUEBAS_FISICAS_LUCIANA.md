# Pruebas de comunicación — Luciana

Estado: pendientes de medición en el montaje real. Una compilación o simulación
no demuestra estos criterios. RNF1 y RNF2 corresponden a Ruben.

## RNF3 — Tiempo de respuesta

Con ESP32 conectado, grabar a 60 fps el simulador y el servo simultáneamente.
Enviar diez órdenes alternadas abierta/cerrada, esperando confirmación entre
ellas. Medir desde Enter hasta el primer movimiento; registrar además
latencia_ms y confirmado del evento comando_puerta en CloudWatch. La latencia
de Lambda es complementaria: no reemplaza la medición de extremo a extremo.
Criterio declarado: cada respuesta física ≤3 s. Informar promedio y máximo.

| Intento | Orden | Cuadro inicial | Cuadro movimiento | Δt (s) | latencia_ms | confirmado | Evidencia |
|---|---|---|---|---|---|---|---|
| 1–10 (una fila por intento) | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |

## RNF4 — Frecuencia de reporte

En el cliente MQTT escuchar únicamente $aws/things/<thing>/shadow/update.
Medir diez intervalos sin eventos: latido 60 s ±1 s. Medir diez cambios del PIR
o del servo: llegada del reporte en ≤1 s con red estable. Conservar marcas de
tiempo del monitor y de MQTT. Separación mínima de eventos: 500 ms, excepto
confirmaciones del actuador y publicación inicial/reconexión prioritarias.

| Ensayo | Tipo | Tiempo del cambio/reporte anterior | Tiempo de reporte | Intervalo | Cumple | Evidencia |
|---|---|---|---|---|---|---|
| pendiente | evento / latido | pendiente | pendiente | pendiente | pendiente | pendiente |

## RNF5 — Reconexión y sincronización

Cerrar la puerta, cortar WiFi 60 s y ordenar abrir durante el corte. Restaurar
la red. Sin enviar otra orden, medir hasta [MQTT] Conectado y movimiento del
servo: objetivo ≤30 s desde que vuelve la red. Guardar video, monitor serie
con delta recibido y Shadow final con desired.puerta = reported.puerta.
Repetir tres veces y registrar los tiempos, fallas y condiciones de red.

| Ensayo | Red restaurada | MQTT conectado | Movimiento | Δt total | desired=reported | Evidencia |
|---|---|---|---|---|---|---|
| 1 | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| 2 | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| 3 | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |

## Preparación de la demo

Copiar include/secrets.example.h a include/secrets.h local y completar WiFi,
endpoint ATS, Thing y PEM. No versionar este archivo. Compilar/cargar
esp32dev-aws (predeterminado). Monitor: 115200 baudios. Confirmar [WiFi]
Conectado, [MQTT] Conectado, shadow/get y, si hay orden pendiente, delta recibido.
Nunca subir el binario compilado con la plantilla de ejemplo para una demo real.
