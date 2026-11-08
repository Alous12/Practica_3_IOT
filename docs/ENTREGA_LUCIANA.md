# Luciana — entrega adaptada a Practica_3_IOT

Esta entrega usa la base correcta Practica_3_IOT.rar. El paquete anterior,
Luciana_objeto_inteligente.zip, corresponde a otra estructura: no usarlo aquí.

## Archivos

- src/core/: interfaces Sensor, Actuator y contrato de transporte ShadowPort.
- src/sensors/: lectura PIR HC-SR501 (RF1).
- src/actuators/: servo SG90 (aplicación de órdenes, RF3).
- src/app/: reportes por cambio/latido y distribución del delta (RF2/RF3).
- src/main.cpp: composición de objetos y selección explícita del transporte.
- include/config.h: pines 27/13, ángulos, tiempos y claves del Shadow.
- platformio.ini: conserva la placa esp32dev de la base.
- docs/anexos/circuito.png y SECCION_2_2_LUCIANA.md.

## Prueba local

Abrir la raíz Practica_3_IOT en PlatformIO; no hay subcarpeta firmware/.
Compilar/cargar el entorno esp32dev. Abrir monitor a 115200 baudios.
Esperar 60 s de calentamiento; mover la mano ante el PIR y revisar JSON LOCAL.
Enviar a para abrir, c para cerrar. No existe control automático PIR→servo.
No se necesitan WiFi, certificados ni cuenta AWS para esta prueba local.

El SG90 se manda a posición y luego se retira PWM tras 700 ms. No se mide su
posición física; verificar el pestillo y calibrar 0/90 grados sin forzarlo.

## Integración pendiente con Alejandro

La base de Alejandro contiene AWS, Lambda y Alexa, pero todavía no incluye
los módulos de firmware net/ ni secrets.example.h.
No se implementaron esas capas ajenas. El entorno esp32dev-aws exige
src/net/ShadowClient.*, WifiConnection.* y TimeSync.*, más include/secrets.h.
El adaptador en main usa la API del código base anterior; Alejandro debe
confirmar que su implementación conserva esas firmas antes de integrarlo.
Solo ese entorno utiliza comandos reales del Shadow; el modo LOCAL no usa AWS.
No versionar secrets.h, claves ni certificados. Las reglas .gitignore de Alejandro ya excluyen secretos y se conservan intactas.

## Informe y pruebas

Integrar SECCION_2_2_LUCIANA.md en §2.2 del informe del equipo. La base contiene Informe_Ale.md, conservado sin cambios; se entrega esta sección aislada para no editar las ajenas.
Ver PRUEBAS_FISICAS_LUCIANA.md para RF1–RF3, estabilidad y reconexión.
No hay fotografías ni mediciones reales aún. No se cargó nada al ESP32.
No se crearon commits ni se publicaron cambios a nombre de Luciana; se conserva
la rama Rama_Ale original en la copia de trabajo. El paquete no incluye .git.
