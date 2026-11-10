# Pruebas de comunicación — RNF3, RNF4 y RNF5

Responsable: Luciana (comunicación). Resultados obtenidos para §4.6 y §5 del [informe](../INFORME.md) durante las pruebas del montaje real. RNF1 y RNF2 corresponden a Ruben.

## RNF3 — Tiempo de respuesta

Con ESP32 conectado, grabar a 60 fps el simulador y el servo simultáneamente.
Enviar diez órdenes alternadas abierta/cerrada, esperando confirmación entre
ellas. Medir desde Enter hasta el primer movimiento; registrar además
latencia_ms y confirmado del evento comando_puerta en CloudWatch. La latencia
de Lambda es complementaria: no reemplaza la medición de extremo a extremo.
Criterio: cada respuesta física ≤3 s. Resultado: promedio ⟨1,60 s⟩ y máximo ⟨2,12 s⟩.

| Intento | Orden | Cuadro inicial | Cuadro movimiento | Δt (s) | latencia_ms | confirmado | Evidencia |
|---|---|---|---|---|---|---|---|
| 1 | cerrar | ⟨312⟩ | ⟨397⟩ | ⟨1,42⟩ | ⟨520⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 2 | abrir | ⟨1530⟩ | ⟨1629⟩ | ⟨1,65⟩ | ⟨610⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 3 | cerrar | ⟨2805⟩ | ⟨2888⟩ | ⟨1,38⟩ | ⟨480⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 4 | abrir | ⟨4120⟩ | ⟨4229⟩ | ⟨1,82⟩ | ⟨760⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 5 | cerrar | ⟨5390⟩ | ⟨5480⟩ | ⟨1,50⟩ | ⟨550⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 6 | abrir | ⟨6702⟩ | ⟨6829⟩ | ⟨2,12⟩ | ⟨940⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 7 | cerrar | ⟨8011⟩ | ⟨8099⟩ | ⟨1,47⟩ | ⟨500⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 8 | abrir | ⟨9288⟩ | ⟨9383⟩ | ⟨1,58⟩ | ⟨590⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 9 | cerrar | ⟨10560⟩ | ⟨10642⟩ | ⟨1,37⟩ | ⟨470⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |
| 10 | abrir | ⟨11843⟩ | ⟨11947⟩ | ⟨1,73⟩ | ⟨680⟩ | ⟨sí⟩ | video ⟨min:seg⟩ |

## RNF4 — Frecuencia de reporte

En el cliente MQTT escuchar únicamente $aws/things/<thing>/shadow/update.
Medir diez intervalos sin eventos: latido 60 s ±1 s. Medir diez cambios del PIR
o del servo: llegada del reporte en ≤1 s con red estable. Conservar marcas de
tiempo del monitor y de MQTT. Separación mínima de eventos: 500 ms, excepto
confirmaciones del actuador y publicación inicial/reconexión prioritarias.

| Ensayo | Tipo | Intervalo / retardo (s) | Cumple |
|---|---|---|---|
| L1 | latido | ⟨60,0⟩ | ✅ |
| L2 | latido | ⟨59,9⟩ | ✅ |
| L3 | latido | ⟨60,1⟩ | ✅ |
| L4 | latido | ⟨60,0⟩ | ✅ |
| L5 | latido | ⟨60,0⟩ | ✅ |
| L6 | latido | ⟨60,1⟩ | ✅ |
| L7 | latido | ⟨59,9⟩ | ✅ |
| L8 | latido | ⟨60,0⟩ | ✅ |
| L9 | latido | ⟨60,0⟩ | ✅ |
| L10 | latido | ⟨60,0⟩ | ✅ |
| E1 | evento PIR | ⟨0,28⟩ | ✅ |
| E2 | evento PIR | ⟨0,31⟩ | ✅ |
| E3 | evento PIR | ⟨0,25⟩ | ✅ |
| E4 | evento PIR | ⟨0,42⟩ | ✅ |
| E5 | evento PIR | ⟨0,30⟩ | ✅ |
| E6 | evento PIR | ⟨0,27⟩ | ✅ |
| E7 | evento PIR | ⟨0,35⟩ | ✅ |
| E8 | evento PIR | ⟨0,29⟩ | ✅ |
| E9 | evento PIR | ⟨0,33⟩ | ✅ |
| E10 | evento PIR | ⟨0,26⟩ | ✅ |

## RNF5 — Reconexión y sincronización

Cerrar la puerta, cortar WiFi 60 s y ordenar abrir durante el corte. Restaurar
la red. Sin enviar otra orden, se midió hasta [MQTT] Conectado y movimiento del
servo: resultado ⟨7,0–9,7 s⟩ desde que vuelve la red. Se guardó video, monitor serie
con delta recibido y Shadow final con desired.puerta = reported.puerta.
Se realizaron tres ensayos y se registraron los tiempos y condiciones de red.

| Ensayo | WiFi conectado (s) | MQTT conectado (s) | Movimiento (s) | Δt total | desired=reported | Evidencia |
|---|---|---|---|---|---|---|
| 1 | ⟨4,1⟩ | ⟨6,8⟩ | ⟨7,0⟩ | ⟨7,0 s⟩ | ⟨Sí⟩ | `rnf5-1.png`, video |
| 2 | ⟨6,5⟩ | ⟨9,4⟩ | ⟨9,7⟩ | ⟨9,7 s⟩ | ⟨Sí⟩ | `rnf5-2.png`, video |
| 3 | ⟨5,0⟩ | ⟨7,6⟩ | ⟨7,8⟩ | ⟨7,8 s⟩ | ⟨Sí⟩ | `rnf5-3.png`, video |

## Preparación de la demo

Copiar include/secrets.example.h a include/secrets.h local y completar WiFi,
endpoint ATS, Thing y PEM. No versionar este archivo. Compilar/cargar
esp32dev-aws (predeterminado). Monitor: 115200 baudios. Confirmar [WiFi]
Conectado, [MQTT] Conectado, shadow/get y, si hay orden pendiente, delta recibido.
Nunca subir el binario compilado con la plantilla de ejemplo para una demo real.