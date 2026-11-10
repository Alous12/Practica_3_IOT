# Pruebas de hardware — RNF1 y RNF2

Responsable: Ruben (hardware). Resultados para §5 del informe y evidencias en `docs/anexos/`.

---

## RNF1 — Estabilidad durante 30 minutos

**Objetivo.** El objeto inteligente funciona 30 min seguidos sin reiniciarse, con el servo moviéndose periódicamente.

**Condiciones**

| Dato | Valor |
|---|---|
| Fecha y hora de inicio | 9 de noviembre de 2026, 22:55:38 (arranque del ensayo válido) |
| Firmware | raíz, entorno **`esp32dev-aws`** (WiFi + MQTT + Shadow), commit `84ac35a`. El entorno `esp32dev` es local y no sirve para esta prueba |
| Alimentación | ESP32 por USB de la computadora · servo y PIR con porta pilas 4 × AA (tensión medida: 5,8–6,2 V) |
| Distancia al router | 3–5 m (RSSI medido entre −48 y −55 dBm) |

**Procedimiento**

1. Encender el ESP32 y abrir el monitor serie. Anotar el minuto 0.
2. Cada 5 min (aproximadamente) dar una orden alternada desde Alexa (o desde *AWS IoT → Thing → Device Shadow → Edit*): cerrar, abrir, cerrar…
3. En cada fila, leer `uptime_s` y `rssi` del `reported` del Shadow (consola de AWS) y verificar que el servo se movió.
4. **Criterio:** `uptime_s` crece siempre (≈ minuto × 60) y nunca vuelve a 0. En el monitor serie no aparece `Brownout detector was triggered` ni `rst:`.

| Minuto | uptime_s | rssi (dBm) | Orden dada | ¿El servo se movió? | ¿Reinicio? |
|---|---|---|---|---|---|
| 0 (22:55:41) | 2 | −49 | — | — | — |
| ≈ 10 (23:06:01) | 623 | −51 | abrir | Sí | No |
| ≈ 15 (23:10:08) | 870 | −51 | cerrar | Sí | No |
| ≈ 20 (23:15:14) | 1176 | −51 | abrir | Sí | No |
| ≈ 25 (23:20:07) | 1469 | −53 | cerrar | Sí | No |
| ≈ 30 (23:25:02) | 1764 | −52 | abrir | Sí | No |
| ≈ 31 (23:26:04) | ≈ 1826 | −50 a −55 | — | — | No |

Valores tomados del monitor serie (línea `reported` que sigue a cada orden); las órdenes se dieron editando `desired.puerta` en la Sombra clásica. Entre el inicio y el minuto 10 no se dio ninguna orden; desde el minuto 10 se dio una cada 5 min aproximadamente, 5 en total. Un primer intento, iniciado a las 22:47, se interrumpió por reinicios `rst:0x1 (POWERON_RESET)` al mover el cable USB y el montaje; no apareció ningún `Brownout`. El ensayo válido empezó en el arranque de las 22:55:38, sin tocar el circuito.

**Resultado:** cumple · reinicios: 0 durante el ensayo válido · `uptime_s` final: ≥ 1800.

**Evidencia:** la tabla anterior, con los valores de `uptime_s` y `rssi` copiados del monitor serie.

---

## RNF2 — Exactitud del PIR

**Objetivo.** El PIR detecta al menos el **95 %** de las pasadas hasta **3 m**, y tiene **0 falsos positivos** en 10 min con la sala vacía.

**Condiciones**

| Dato | Valor |
|---|---|
| Fecha | 9 de noviembre de 2026 |
| Ajustes del HC-SR501 | jumper **L** (de fábrica) · Tx al mínimo (pulso medido ~1,2 s, bloqueo ~5 s) · Sx de fábrica, sin modificar |
| Altura del PIR | 100 cm sobre el piso |
| Firmware | [`tools/prueba_hardware`](../../tools/prueba_hardware/src/main.cpp) (monitor serie, comando `r`) o el de la raíz con `esp32dev-aws` (Shadow) |
| Lugar | dormitorio, luz artificial, sin calefactores ni ventanas al sol frente al PIR |

**Procedimiento**

1. Encender y esperar a que el monitor muestre `sensor_listo=true` (~60 s).
2. Marcar en el piso 1, 2, 3 y 4 m frente al PIR con cinta métrica.
3. Para cada distancia: enviar `r` (reinicia el conteo), hacer **20 pasadas** caminando de lado a lado a velocidad normal, **esperando ≥ 7 s quieto y fuera del campo entre pasadas** (pulso ~1,2 s más bloqueo ~5 s del modo L; si no, la siguiente pasada no se detecta).
4. Anotar `detecciones` al final (conteo del monitor; con el firmware completo, la diferencia de `detecciones` en el Shadow antes y después).
5. **Prueba de falsos positivos:** con la sala vacía y nadie en el campo del PIR, `r` y esperar 10 min. Anotar las detecciones.

| Distancia (m) | Intentos | Detectadas | % | Meta |
|---|---|---|---|---|
| 1 | 20 | 20 | 100 % | ≥ 95 % |
| 2 | 20 | 20 | 100 % | ≥ 95 % |
| 3 | 20 | 19 | 95 % | ≥ 95 % |
| 4 | 20 | 15 | 75 % | informativa |

| Prueba | Duración | Detecciones | Meta |
|---|---|---|---|
| Sala vacía | 10 min | 0 | 0 |

**Resultado:** cumple · alcance efectivo observado: 3 m (98,3 % en el rango 1–3 m).

**Datos crudos** en [`deteccion.csv`](deteccion.csv):

```csv
prueba,distancia_m,intentos,detectadas,porcentaje
pasadas,1,20,20,100
pasadas,2,20,20,100
pasadas,3,20,19,95
pasadas,4,20,15,75
sala_vacia_10min,,0,0,
```

**Evidencia:** [`deteccion.csv`](deteccion.csv), con los conteos de cada distancia y de la sala vacía.