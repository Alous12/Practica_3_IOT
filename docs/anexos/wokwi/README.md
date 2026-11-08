# Circuito en Wokwi (circuito.png)

Responsable: Ruben (hardware).

1. Entrar a <https://wokwi.com> → **New project** → **ESP32**.
2. En la pestaña `diagram.json` borrar todo y pegar el contenido de [`diagram.json`](diagram.json).
3. Ordenar los cables con el mouse si se cruzan (no cambia las conexiones).
4. Exportar la imagen: clic derecho sobre el lienzo → *Save as image* (o captura de pantalla) y guardarla como `docs/anexos/circuito.png`.

| Componente | Pin | ESP32 | Color del cable |
|---|---|---|---|
| PIR HC-SR501 | VCC | VIN (5 V) | rojo |
| PIR HC-SR501 | OUT | GPIO 27 (D27) | verde |
| PIR HC-SR501 | GND | GND | negro |
| Servo SG90 | V+ (rojo) | VIN (5 V) | rojo |
| Servo SG90 | PWM (naranja) | GPIO 13 (D13) | naranja |
| Servo SG90 | GND (marrón) | GND | negro |

**Condensador de 470 µF / 16 V.** Wokwi no tiene condensador electrolítico entre sus piezas estándar, así que no aparece en el diagrama. En el montaje físico va entre VIN (+) y GND (−), lo más cerca posible del servo. En el informe (§2.2) se indica que está solo en la protoboard.

**Para simular (opcional).** El diagrama sirve con el código de [`firmware/tools/prueba_hardware`](../../../firmware/tools/prueba_hardware/src/main.cpp): en Wokwi, el PIR se activa con el botón *Simulate motion*.
