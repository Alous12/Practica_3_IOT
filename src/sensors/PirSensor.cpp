#include "sensors/PirSensor.h"

#include <Arduino.h>

#include "config.h"
#include <time.h>

PirSensor::PirSensor(uint8_t pin, unsigned long warmupMs) : pin_(pin), warmupMs_(warmupMs) {}

void PirSensor::begin() {
  pinMode(pin_, INPUT);
  startedMs_ = millis();
  ready_ = false;
  motion_ = false;
  detections_ = 0;
  lastDetectionEpoch_ = 0;
}

bool PirSensor::update(unsigned long nowMs) {
  bool becameReady = false;
  if (!ready_) {
    // Resta sin signo: también funciona si millis() desborda.
    if (nowMs - startedMs_ < warmupMs_) {
      return false;  // el módulo aún se está estabilizando
    }
    ready_ = true;
    Serial.println("[PIR] Calentamiento terminado, sensor listo");
    becameReady = true;  // leer también el nivel presente al terminar la espera
  }

  bool level = digitalRead(pin_) == HIGH;
  if (level == motion_) {
    return becameReady;  // reportar sensor_listo aunque el nivel no cambie
  }

  motion_ = level;
  if (motion_) {
    detections_++;
    const time_t epoch = time(nullptr);
    lastDetectionEpoch_ = epoch >= 1704067200
                              ? static_cast<uint32_t>(epoch) : 0;
    // La sincronización NTP la proporciona la capa de red, si está disponible.
    Serial.printf("[PIR] Movimiento detectado (#%u)\n", detections_);
  } else {
    Serial.println("[PIR] Sin movimiento");
  }
  return true;
}

void PirSensor::report(JsonObject reported) const {
  reported[KEY_MOTION] = motion_;
  reported[KEY_DETECTIONS] = detections_;
  reported[KEY_LAST_DETECTION] = lastDetectionEpoch_;
  reported[KEY_SENSOR_READY] = ready_;
}
