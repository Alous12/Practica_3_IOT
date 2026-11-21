#pragma once

#include "core/Setting.h"

/**
 * Requerimientos: RF3 (aplicar desired) y RF2 (reporte).
 *
 * Parámetro entero con rango cerrado [minValue, maxValue] (p. ej. "max_detecciones"
 * o "ventana_min"). Solo acepta enteros JSON dentro del rango: textos, decimales,
 * booleanos o valores fuera de rango se ignoran y se conserva el valor actual.
 */
class IntSetting : public Setting {
 public:
  /** key debe ser una constante de vida estática (las KEY_* de config.h). */
  IntSetting(const char *key, int defaultValue, int minValue, int maxValue);

  const char *key() const override { return key_; }
  bool applyDesired(JsonVariantConst value) override;
  void report(JsonObject reported) const override;

  int value() const { return value_; }

 private:
  const char *key_;
  int value_;
  int minValue_;
  int maxValue_;
};
