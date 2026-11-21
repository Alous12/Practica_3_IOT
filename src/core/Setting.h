#pragma once

#include <ArduinoJson.h>

/**
 * Requerimientos: RF3 (aplicar desired) y RF2 (reporte).
 *
 * Interfaz común de los parámetros de configuración controlados desde el Shadow
 * (modo de operación, umbrales, ventanas de tiempo...).
 *
 * A diferencia de un Actuator, un Setting no mueve hardware: solo guarda un valor
 * validado. Cada uno es dueño de UNA clave del documento (key()). Cuando llega un
 * delta con esa clave, SmartObject llama a applyDesired(). Para agregar otro
 * parámetro basta con heredar de esta clase y registrarlo con SmartObject::addSetting().
 */
class Setting {
 public:
  virtual ~Setting() = default;

  /** Nombre del atributo del Shadow (p. ej. "modo"). */
  virtual const char *key() const = 0;

  /**
   * Aplica el valor deseado recibido en el delta.
   * Devuelve true solo si el valor era válido y distinto del actual (cambió).
   * Un valor inválido se ignora y se registra en el log.
   */
  virtual bool applyDesired(JsonVariantConst value) = 0;

  /** Escribe su valor actual dentro de state.reported. */
  virtual void report(JsonObject reported) const = 0;
};
