# Pruebas de hardware — RNF1 y RNF2

Responsable: Ruben (hardware). Resultados para §5 del informe y evidencias en `docs/anexos/`.

---

## RNF1 — Estabilidad durante 30 minutos

**Objetivo.** El objeto inteligente funciona 30 min seguidos sin reiniciarse, con el servo moviéndose periódicamente.

**Condiciones**

| Dato | Valor |
|---|---|
| Fecha y hora de inicio | [COMPLETAR] |
| Firmware | completo (WiFi + MQTT + Shadow), commit [COMPLETAR] |
| Alimentación | USB de [COMPLETAR: laptop / cargador 5 V] · servo por [COMPLETAR: VIN / fuente aparte] |
| Distancia al router | [COMPLETAR] m |

**Procedimiento**

1. Encender el ESP32 y abrir el monitor serie. Anotar el minuto 0.
2. Cada 5 min dar una orden alternada desde Alexa (o desde *AWS IoT → Thing → Device Shadow → Edit*): cerrar, abrir, cerrar…
3. En cada fila, leer `uptime_s` y `rssi` del `reported` del Shadow (consola de AWS) y verificar que el servo se movió.
4. **Criterio:** `uptime_s` crece siempre (≈ minuto × 60) y nunca vuelve a 0. En el monitor serie no aparece `Brownout detector was triggered` ni `rst:`.

| Minuto | uptime_s | rssi (dBm) | Orden dada | ¿El servo se movió? | ¿Reinicio? |
|---|---|---|---|---|---|
| 0 | | | — | — | |
| 5 | | | cerrar | | |
| 10 | | | abrir | | |
| 15 | | | cerrar | | |
| 20 | | | abrir | | |
| 25 | | | cerrar | | |
| 30 | | | abrir | | |

**Resultado:** [COMPLETAR: cumple / no cumple] · reinicios: [COMPLETAR] · `uptime_s` final: [COMPLETAR] (esperado ≥ 1800).

**Evidencias:** `rnf1-shadow-min0.png`, `rnf1-shadow-min30.png` (Shadow con `uptime_s`) y `rnf1-monitor.png` (monitor serie sin reinicios).

---

## RNF2 — Exactitud del PIR

**Objetivo.** El PIR detecta al menos el **95 %** de las pasadas hasta **3 m**, y tiene **0 falsos positivos** en 10 min con la sala vacía.

**Condiciones**

| Dato | Valor |
|---|---|
| Fecha | [COMPLETAR] |
| Ajustes del HC-SR501 | jumper **H** · Tx al mínimo (~3 s) · Sx [COMPLETAR: posición, p. ej. medio] |
| Altura del PIR | [COMPLETAR] cm sobre el piso |
| Firmware | `firmware/tools/prueba_hardware` (monitor serie) o firmware completo (Shadow) |
| Lugar | [COMPLETAR: sala, iluminación, sin calefactores ni ventanas al sol frente al PIR] |

**Procedimiento**

1. Encender y esperar a que el monitor muestre `sensor_listo=true` (~60 s).
2. Marcar en el piso 1, 2, 3 y 4 m frente al PIR con cinta métrica.
3. Para cada distancia: enviar `r` (reinicia el conteo), hacer **20 pasadas** caminando de lado a lado a velocidad normal, **esperando ≥ 5 s quieto y fuera del campo entre pasadas** (Tx ≈ 3 s; si no, dos pasadas se juntan en una sola detección).
4. Anotar `detecciones` al final (conteo del monitor; con el firmware completo, la diferencia de `detecciones` en el Shadow antes y después).
5. **Prueba de falsos positivos:** con la sala vacía y nadie en el campo del PIR, `r` y esperar 10 min. Anotar las detecciones.

| Distancia (m) | Intentos | Detectadas | % | Meta |
|---|---|---|---|---|
| 1 | 20 | | | ≥ 95 % |
| 2 | 20 | | | ≥ 95 % |
| 3 | 20 | | | ≥ 95 % |
| 4 | 20 | | | informativa |

| Prueba | Duración | Detecciones | Meta |
|---|---|---|---|
| Sala vacía | 10 min | | 0 |

**Resultado:** [COMPLETAR: cumple / no cumple] · alcance efectivo observado: [COMPLETAR] m.

**Datos crudos** en `docs/anexos/deteccion.csv` (nombre pedido en `docs/anexos/README.md`), con este formato:

```csv
prueba,distancia_m,intentos,detectadas,porcentaje
pasadas,1,20,,
pasadas,2,20,,
pasadas,3,20,,
pasadas,4,20,,
sala_vacia_10min,,0,,
```

**Evidencias:** `rnf2-montaje.jpg` (cinta métrica y PIR) y `rnf2-monitor.png` (conteo de una distancia).
