#pragma once

#include "config.h"
#include "core/Setting.h"

/**
 * Requerimientos: RF3 (aplicar desired) y RF2 (reporte).
 *
 * Modo de operación del objeto inteligente. Atributo del Shadow: "modo" =
 *   · "manual"     : la puerta solo se mueve por orden explícita (valor inicial);
 *   · "automatico" : se permite el cierre automático;
 *   · "bloqueo"    : se permite el cierre automático (modo de máxima seguridad).
 * Cualquier otro valor se ignora.
 */
class OperatingMode : public Setting {
 public:
  const char *key() const override;
  bool applyDesired(JsonVariantConst value) override;
  void report(JsonObject reported) const override;

  /** Modo actual (siempre una de las constantes MODE_* de config.h). */
  const char *value() const { return value_; }

  /** true si el modo permite cerrar la puerta automáticamente ("automatico" o "bloqueo"). */
  bool autoLockEnabled() const;

 private:
  // Apunta a una constante MODE_*, nunca al búfer JSON (se libera tras el delta).
  const char *value_ = MODE_MANUAL;
};
