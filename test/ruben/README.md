# Prueba del hardware (Ruben)

Comprueba el filtro de 50 ms del PIR (pulsos de ruido en alto y en bajo), que no se cuenten detecciones durante el calentamiento y la calibración del servo. No usa ESP32: compila los `.cpp` reales con g++ y los stubs de `test/luciana/stubs/`.

Ejecutar desde la raíz, después de `pio run -e esp32dev` (descarga ArduinoJson):

```
g++ -std=c++17 -Wall -Wextra -I test/luciana/stubs -I src -I include -I .pio/libdeps/esp32dev/ArduinoJson/src test/ruben/test_hardware.cpp src/sensors/PirSensor.cpp src/actuators/DoorLock.cpp -o test_hardware.exe && ./test_hardware.exe
```

Salida esperada: `OK: filtro del PIR ...`. No cargar este binario al ESP32.
