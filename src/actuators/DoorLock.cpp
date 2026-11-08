#include "actuators/DoorLock.h"

#include <Arduino.h>

#include "config.h"

DoorLock::DoorLock(uint8_t pin, int closedAngle, int openAngle, unsigned long settleMs)
    : pin_(pin), closedAngle_(closedAngle), openAngle_(openAngle), settleMs_(settleMs) {}

const char *DoorLock::key() const { return KEY_DOOR; }

void DoorLock::begin() {
  servo_.setPeriodHertz(50);  // SG90: 50 Hz
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
    servo_.attach(pin_, 500, 2400);  // pulsos típicos del SG90 (µs)
  }
  servo_.write(closed ? closedAngle_ : openAngle_);
  closed_ = closed;
  moving_ = true;
  moveStartedMs_ = millis();
  Serial.printf("[Puerta] %s\n", closed ? "Cerrando" : "Abriendo");
}
