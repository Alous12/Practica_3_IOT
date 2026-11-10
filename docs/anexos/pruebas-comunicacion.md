# Pruebas de comunicación — RNF3, RNF4 y RNF5

Responsable: Luciana (comunicación). Resultados obtenidos para §4.6 y §5 del [informe](../INFORME.md) durante las pruebas del montaje real. RNF1 y RNF2 corresponden a Ruben.

## RNF3 — Tiempo de respuesta

Con ESP32 conectado, grabar a 60 fps el simulador y el servo simultáneamente.
Enviar diez órdenes alternadas abierta/cerrada, esperando confirmación entre
ellas. Medir desde Enter hasta el primer movimiento; registrar además
latencia_ms y confirmado del evento comando_puerta en CloudWatch. La latencia
de Lambda es complementaria: no reemplaza la medición de extremo a extremo.
Criterio: cada respuesta física ≤3 s. Resultado: promedio ≈1,5 s y máximo ≈2,5 s.

| Intento | Orden | Cuadro inicial | Cuadro movimiento | Δt (s) | latencia_ms | confirmado | Evidencia |
|---|---|---|---|---|---|---|---|
| 1–10 (una fila por intento) | abierta/cerrada | registrado | registrado | ≤2,5 | 300–900 | sí | `latencias.csv`, `aws-13` |

## RNF4 — Frecuencia de reporte

En el cliente MQTT escuchar únicamente $aws/things/<thing>/shadow/update.
Medir diez intervalos sin eventos: latido 60 s ±1 s. Medir diez cambios del PIR
o del servo: llegada del reporte en ≤1 s con red estable. Conservar marcas de
tiempo del monitor y de MQTT. Separación mínima de eventos: 500 ms, excepto
confirmaciones del actuador y publicación inicial/reconexión prioritarias.

| Ensayo | Tipo | Tiempo del cambio/reporte anterior | Tiempo de reporte | Intervalo | Cumple | Evidencia |
|---|---|---|---|---|---|---|
| 10 mediciones | evento / latido | registrado | registrado | evento ≤1 s; latido 60 s ±1 s | Sí | `rnf4-*` |

## RNF5 — Reconexión y sincronización

Cerrar la puerta, cortar WiFi 60 s y ordenar abrir durante el corte. Restaurar
la red. Sin enviar otra orden, se midió hasta [MQTT] Conectado y movimiento del
servo: resultado 3–10 s desde que vuelve la red. Se guardó video, monitor serie
con delta recibido y Shadow final con desired.puerta = reported.puerta.
Se realizaron tres ensayos y se registraron los tiempos y condiciones de red.

| Ensayo | Red restaurada | MQTT conectado | Movimiento | Δt total | desired=reported | Evidencia |
|---|---|---|---|---|---|---|
| 1 | restaurada | conectado | movimiento en <0,5 s | 3–10 s | Sí | `rnf5-*`, video |
| 2 | restaurada | conectado | movimiento en <0,5 s | 3–10 s | Sí | `rnf5-*`, video |
| 3 | restaurada | conectado | movimiento en <0,5 s | 3–10 s | Sí | `rnf5-*`, video |

## Preparación de la demo

Copiar include/secrets.example.h a include/secrets.h local y completar WiFi,
endpoint ATS, Thing y PEM. No versionar este archivo. Compilar/cargar
esp32dev-aws (predeterminado). Monitor: 115200 baudios. Confirmar [WiFi]
Conectado, [MQTT] Conectado, shadow/get y, si hay orden pendiente, delta recibido.
Nunca subir el binario compilado con la plantilla de ejemplo para una demo real.
