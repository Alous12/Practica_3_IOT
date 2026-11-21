/**
 * Implementación del parámetro entero con rango (RF3).
 */
#include "settings/IntSetting.h"

#include <Arduino.h>

IntSetting::IntSetting(const char *key, int defaultValue, int minValue, int maxValue)
    : key_(key), value_(defaultValue), minValue_(minValue), maxValue_(maxValue) {}

bool IntSetting::applyDesired(JsonVariantConst value) {
  if (!value.is<int>()) {
    Serial.printf("[Ajuste] %s: valor deseado inválido (se espera entero)\n", key_);
    return false;
  }
  const int desired = value.as<int>();
  if (desired < minValue_ || desired > maxValue_) {
    Serial.printf("[Ajuste] %s: %d fuera de rango [%d, %d] (se ignora)\n", key_, desired,
                  minValue_, maxValue_);
    return false;
  }
  if (desired == value_) {
    return false;  // sin cambio
  }
  value_ = desired;
  Serial.printf("[Ajuste] %s = %d\n", key_, value_);
  return true;
}

void IntSetting::report(JsonObject reported) const { reported[key_] = value_; }
