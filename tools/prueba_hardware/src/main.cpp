/**
 * Banco de pruebas del hardware: PIR + servo, sin WiFi ni AWS.
 * Capa: hardware (Ruben).
 *
 * Sirve para: RNF2 (exactitud del PIR), calibrar SERVO_ANGLE_CLOSED / SERVO_ANGLE_OPEN
 * y revisar que el servo no provoque reinicios por brownout.
 * Usa las clases reales PirSensor y DoorLock y los valores de include/config.h.
 *
 * Monitor serie a 115200 baudios. Comandos (una letra):
 *   c  cerrar la puerta          a  abrir la puerta
 *   +  servo +5°                 -  servo -5°        (calibración; muestra el ángulo)
 *   r  reiniciar el contador de detecciones (antes de cada distancia del RNF2)
 *   s  mostrar el estado
 */
#include <Arduino.h>
#include <esp_system.h>

#include "actuators/DoorLock.h"
#include "config.h"
#include "sensors/PirSensor.h"

namespace {
PirSensor pir(PIR_PIN, PIR_WARMUP_MS);
DoorLock door(SERVO_PIN, SERVO_ANGLE_CLOSED, SERVO_ANGLE_OPEN, SERVO_SETTLE_MS);

int calibAngle = SERVO_ANGLE_CLOSED;
uint32_t countOffset = 0;  // reinicia el conteo sin tocar PirSensor
unsigned long lastStatusMs = 0;

void printStatus() {
  JsonDocument doc;
  JsonObject reported = doc.to<JsonObject>();
  pir.report(reported);
  door.report(reported);
  Serial.printf("[%6lu s] sensor_listo=%s movimiento=%s detecciones=%lu puerta=%s\n",
                millis() / 1000UL,
                reported[KEY_SENSOR_READY].as<bool>() ? "true" : "false",
                reported[KEY_MOTION].as<bool>() ? "true" : "false",
                static_cast<unsigned long>(reported[KEY_DETECTIONS].as<uint32_t>() - countOffset),
                reported[KEY_DOOR].as<const char *>());
}

void order(const char *value) {
  JsonDocument doc;
  doc.set(value);
  door.applyDesired(doc.as<JsonVariantConst>());  // mismo camino que un delta del Shadow
}
}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(300);
  Serial.printf("\nMotivo del último reinicio: %d (1=encendido, 15=brownout)\n",
                static_cast<int>(esp_reset_reason()));
  pir.begin();
  door.begin();
  Serial.println("Prueba de hardware. Esperar ~60 s de calentamiento del PIR.");
  Serial.println("Comandos: c=cerrar a=abrir +/-=calibrar r=reiniciar conteo s=estado");
}

void loop() {
  const unsigned long now = millis();
  door.loop(now);
  if (pir.update(now)) printStatus();  // cada evento del PIR
  if (now - lastStatusMs >= 10000) {   // y un estado cada 10 s
    lastStatusMs = now;
    printStatus();
  }

  if (!Serial.available()) return;
  switch (Serial.read()) {
    case 'c': order(DOOR_CLOSED); calibAngle = SERVO_ANGLE_CLOSED; printStatus(); break;
    case 'a': order(DOOR_OPEN);   calibAngle = SERVO_ANGLE_OPEN;   printStatus(); break;
    case '+': calibAngle = min(calibAngle + 5, 180); door.calibrate(calibAngle);
              Serial.printf("Ángulo de calibración: %d\n", calibAngle); break;
    case '-': calibAngle = max(calibAngle - 5, 0); door.calibrate(calibAngle);
              Serial.printf("Ángulo de calibración: %d\n", calibAngle); break;
    case 'r': {
      JsonDocument doc;
      pir.report(doc.to<JsonObject>());
      countOffset = doc[KEY_DETECTIONS].as<uint32_t>();
      Serial.println("Conteo reiniciado.");
      break;
    }
    case 's': printStatus(); break;
    default: break;
  }
}
