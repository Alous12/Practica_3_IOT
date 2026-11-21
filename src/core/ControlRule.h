#pragma once

#include <ArduinoJson.h>

/** Regla local: se evalua despues de leer sensores, incluso sin transporte. */
class ControlRule {
 public:
  virtual ~ControlRule() = default;
  // true solo si cambio el estado de un actuador en este ciclo.
  virtual bool evaluate(JsonObjectConst reported) = 0;
  // Agrega los atributos de desired que deben retirarse tras una accion local.
  virtual void clearDesired(JsonObject desired) const = 0;
};
