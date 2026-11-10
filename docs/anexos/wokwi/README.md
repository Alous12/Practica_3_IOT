# Circuito en Wokwi (circuito-wokwi.png)

Responsable: Ruben (hardware).

El diagrama principal del informe es `docs/anexos/circuito.png` (con el porta pilas de 4 × AA). Este diagrama de Wokwi es la versión simulable del mismo circuito y se guarda aparte como `circuito-wokwi.png`.

1. Entrar a <https://wokwi.com> → **New project** → **ESP32**.
2. En la pestaña `diagram.json` borrar todo y pegar el contenido de [`diagram.json`](diagram.json).
3. Ordenar los cables con el mouse si se cruzan (no cambia las conexiones).
4. Exportar la imagen (clic derecho sobre el lienzo → *Save as image*, o captura) y guardarla como `docs/anexos/circuito-wokwi.png`.

| Componente | Pin | ESP32 | Color del cable |
|---|---|---|---|
| PIR HC-SR501 | VCC | VIN (5 V) | rojo |
| PIR HC-SR501 | OUT | GPIO 27 (D27) | verde |
| PIR HC-SR501 | GND | GND | negro |
| Servo SG90 | V+ (rojo) | VIN (5 V) | rojo |
| Servo SG90 | PWM (naranja) | GPIO 25 (D25) | naranja |
| Servo SG90 | GND (marrón) | GND | negro |

**Alimentación.** Wokwi no tiene porta pilas entre sus piezas estándar, así que en la simulación el PIR y el servo toman 5 V de VIN. En el montaje físico se alimentan con un porta pilas de 4 × AA (6 V) cuyo negativo se une al GND del ESP32, y el ESP32 se alimenta por USB (ver `circuito.png` y `circuito-3d.svg`).
