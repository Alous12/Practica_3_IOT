# Validación — Luciana sobre la base actualizada de Alejandro

- Base: Practica_3_IOT.rar recibido después de incorporar Rama_Ale.
- Se modifican únicamente src/main.cpp y platformio.ini de los archivos existentes.
- Se añaden los módulos, configuración, documentos y pruebas de Luciana.
- AWS, Alexa, Lambda, Informe_Ale.md, README, .gitignore y el flujo de pruebas
  de Alejandro conservan exactamente sus bytes originales (comparación SHA-256).
- Compilación real: PlatformIO esp32dev, SUCCESS, 8 de noviembre de 2026.
  RAM 25 408 bytes (7,8%); flash 302 161 bytes (23,1%).
- Prueba C++ del PIR, servo y reportes con dobles de hardware: todas las aserciones pasan.
- Pruebas existentes de Lambda y contratos: 57 passed, 1 skipped en 6,26 s.
  La omitida requiere secrets.example.h, ausente en la base y perteneciente
  a la capa de conectividad. Las cuatro pruebas de config.h ya se ejecutan.
- Entorno predeterminado LOCAL: no se conecta a AWS ni demuestra comunicación MQTT.
- esp32dev-aws necesita net/ y secrets.h; esa integración no se compiló ni probó
  porque no está incluida en la base de Alejandro. El adaptador es el punto de unión.
- No se cargó nada al ESP32. Montaje, calibración y mediciones físicas pendientes.
- El ZIP no lleva .git, credenciales, cachés ni binarios.

## Archivos modificados de la base

- platformio.ini
- src/main.cpp

## Archivos nuevos de Luciana

- docs/ENTREGA_LUCIANA.md
- docs/PRUEBAS_FISICAS_LUCIANA.md
- docs/SECCION_2_2_LUCIANA.md
- docs/anexos/circuito.png
- include/config.h
- src/actuators/DoorLock.cpp
- src/actuators/DoorLock.h
- src/app/SmartObject.cpp
- src/app/SmartObject.h
- src/core/Actuator.h
- src/core/Sensor.h
- src/core/ShadowPort.h
- src/sensors/PirSensor.cpp
- src/sensors/PirSensor.h
- test/luciana/README.md
- test/luciana/stubs/Arduino.h
- test/luciana/stubs/ESP32Servo.h
- test/luciana/stubs/WiFi.h
- test/luciana/stubs/net/ShadowClient.h
- test/luciana/stubs/net/TimeSync.h
- test/luciana/test_firmware.cpp
