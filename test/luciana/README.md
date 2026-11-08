# Prueba de comportamiento del firmware

No usa ESP32, AWS ni credenciales. Los .cpp de producción se compilan con g++ y
ArduinoJson real, sustituyendo solo reloj/GPIO/servo/transporte para la prueba.
Ejecutar desde la raíz después de pio run -e esp32dev:

```
g++ -std=c++17 -Wall -Wextra -I test/luciana/stubs -I src -I include -I .pio/libdeps/esp32dev/ArduinoJson/src test/luciana/test_firmware.cpp src/sensors/PirSensor.cpp src/actuators/DoorLock.cpp src/app/SmartObject.cpp -o test/luciana/test_firmware.exe
```

Ejecutar el binario. Se comprueban calentamiento, conteo por flanco, temporizador
con desborde, comandos inválidos, PWM de 700 ms, evento, latido, confirmación,
reintento y reporte al reconectar el transporte simulado. No incluir los stubs
en src/ ni cargar el binario de pruebas al ESP32.
