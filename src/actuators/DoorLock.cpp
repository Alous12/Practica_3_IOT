/**
 * Implementación de la cerradura con servo SG90 (RF3).
 * Capa: hardware (Ruben).
 *
 * El servo solo recibe PWM mientras se mueve (settleMs) y luego se suelta, para evitar
 * vibraciones y picos de consumo (brownout). El pestillo debe mantener su posición sin fuerza.
 */
#include "actuators/DoorLock.h"

#include <Arduino.h>

#include "config.h"

namespace {
// Pulso del SG90 a 50 Hz: ~500 µs = 0° y ~2400 µs = 180°.
constexpr int SERVO_MIN_US = 500;
constexpr int SERVO_MAX_US = 2400;
}  // namespace

DoorLock::DoorLock(uint8_t pin, int closedAngle, int openAngle, unsigned long settleMs)
    : pin_(pin), closedAngle_(closedAngle), openAngle_(openAngle), settleMs_(settleMs) {}

const char *DoorLock::key() const { return KEY_DOOR; }

void DoorLock::begin() {
  servo_.setPeriodHertz(50);  // SG90: 50 Hz (periodo de 20 ms)
  moveTo(true);               // al encender, la puerta queda cerrada
}

void DoorLock::loop(unsigned long nowMs) {
  if (moving_ && nowMs - moveStartedMs_ >= settleMs_) {
    servo_.detach();
    moving_ = false;
  }
}

bool DoorLock::applyDesired(JsonVariantConst value) {
  const char *text = value.is<const char *>() ? value.as<const char *>() : nullptr;
  if (text == nullptr) {
    Serial.println("[Puerta] Valor deseado inválido (se espera texto)");
    return false;
  }
  if (strcmp(text, DOOR_CLOSED) == 0) {
    moveTo(true);
  } else if (strcmp(text, DOOR_OPEN) == 0) {
    moveTo(false);
  } else {
    Serial.printf("[Puerta] Valor deseado desconocido: %s\n", text);
    return false;
  }
  return true;
}

void DoorLock::report(JsonObject reported) const {
  reported[KEY_DOOR] = closed_ ? DOOR_CLOSED : DOOR_OPEN;
}

void DoorLock::moveTo(bool closed) {
  if (!servo_.attached()) {
    servo_.attach(pin_, SERVO_MIN_US, SERVO_MAX_US);
  }
  servo_.write(closed ? closedAngle_ : openAngle_);
  closed_ = closed;
  moving_ = true;
  moveStartedMs_ = millis();
  Serial.printf("[Puerta] %s\n", closed ? "Cerrando" : "Abriendo");
}

void DoorLock::calibrate(int angle) {
  if (!servo_.attached()) {
    servo_.attach(pin_, SERVO_MIN_US, SERVO_MAX_US);
  }
  servo_.write(angle < 0 ? 0 : (angle > 180 ? 180 : angle));
  moving_ = true;  // loop() lo suelta tras settleMs_, igual que un movimiento normal
  moveStartedMs_ = millis();
}
