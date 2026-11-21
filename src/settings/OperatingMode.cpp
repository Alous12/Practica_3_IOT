/**
 * Implementación del modo de operación (RF3).
 *
 * Solo acepta los tres modos de config.h; se comparan con strcmp y se guarda
 * el puntero a la constante, no al texto recibido.
 */
#include "settings/OperatingMode.h"

#include <Arduino.h>

namespace {
const char *const VALID_MODES[] = {MODE_MANUAL, MODE_AUTO, MODE_LOCKDOWN};
}  // namespace

const char *OperatingMode::key() const { return KEY_MODE; }

bool OperatingMode::applyDesired(JsonVariantConst value) {
  const char *text = value.is<const char *>() ? value.as<const char *>() : nullptr;
  if (text == nullptr) {
    Serial.println("[Modo] Valor deseado inválido (se espera texto)");
    return false;
  }
  for (const char *mode : VALID_MODES) {
    if (strcmp(text, mode) == 0) {
      if (strcmp(value_, mode) == 0) {
        return false;  // ya estaba en ese modo
      }
      value_ = mode;
      Serial.printf("[Modo] Cambiado a %s\n", value_);
      return true;
    }
  }
  Serial.printf("[Modo] Valor deseado desconocido: %s (se ignora)\n", text);
  return false;
}

void OperatingMode::report(JsonObject reported) const { reported[KEY_MODE] = value_; }

bool OperatingMode::autoLockEnabled() const {
  return strcmp(value_, MODE_AUTO) == 0 || strcmp(value_, MODE_LOCKDOWN) == 0;
}
