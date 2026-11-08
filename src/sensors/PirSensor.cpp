/**
 * Implementación del sensor PIR HC-SR501 (RF1).
 * Capa: hardware (Ruben).
 *
 * Todas las comparaciones de tiempo son restas sin signo (ahora - inicio), que siguen
 * funcionando cuando millis() se desborda a los ~49 días.
 */
#include "sensors/PirSensor.h"

#include <Arduino.h>

#include "config.h"
#include <time.h>

PirSensor::PirSensor(uint8_t pin, unsigned long warmupMs, unsigned long debounceMs)
    : pin_(pin), warmupMs_(warmupMs), debounceMs_(debounceMs) {}

void PirSensor::begin() {
  // El HC-SR501 maneja OUT activamente. El pull-down interno evita lecturas flotantes
  // (falsos positivos) si el cable de OUT se suelta. INPUT_PULLDOWN existe en el ESP32;
  // la alternativa INPUT solo se usa al compilar las pruebas en la PC.
#ifdef INPUT_PULLDOWN
  pinMode(pin_, INPUT_PULLDOWN);
#else
  pinMode(pin_, INPUT);
#endif
  startedMs_ = millis();
  ready_ = false;
  motion_ = false;
  rawLevel_ = false;
  rawSinceMs_ = startedMs_;
  detections_ = 0;
  lastDetectionEpoch_ = 0;
}

bool PirSensor::update(unsigned long nowMs) {
  bool becameReady = false;
  if (!ready_) {
    // Durante el calentamiento el módulo da pulsos falsos: no se lee ni se cuenta nada.
    if (nowMs - startedMs_ < warmupMs_) {
      return false;
    }
    ready_ = true;
    Serial.println("[PIR] Calentamiento terminado, sensor listo");
    becameReady = true;  // reportar sensor_listo=true aunque el nivel no cambie
  }

  // Filtro (debounce): un nivel nuevo se acepta solo si se mantuvo debounceMs_.
  const bool level = digitalRead(pin_) == HIGH;
  if (level != rawLevel_) {
    rawLevel_ = level;
    rawSinceMs_ = nowMs;
  }
  if (level == motion_ || nowMs - rawSinceMs_ < debounceMs_) {
    return becameReady;
  }

  motion_ = level;
  if (motion_) {  // flanco de subida = una detección nueva
    detections_++;
    // Hora real si TimeSync (capa de red) ya sincronizó NTP; si no, 0 = sin hora.
    const time_t epoch = time(nullptr);
    lastDetectionEpoch_ = epoch >= 1704067200 ? static_cast<uint32_t>(epoch) : 0;
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
