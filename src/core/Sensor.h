#pragma once

#include <ArduinoJson.h>

/**
 * Requerimientos: RF1 (captura) y RF2 (reporte).
 *
 * Interfaz común de todos los sensores del objeto inteligente.
 *
 * Para agregar un sensor nuevo (p. ej. la LDR de la barrera láser) basta con
 * heredar de esta clase y registrarlo con SmartObject::addSensor(); no hay que
 * tocar la lógica de MQTT ni del Shadow.
 */
class Sensor {
 public:
  virtual ~Sensor() = default;

  /** Configura pines y estado inicial. Se llama una vez en setup(). */
  virtual void begin() = 0;

  /**
 * Requerimientos: RF1 (captura) y RF2 (reporte).
 *
   * Lee el sensor. Devuelve true si hubo un cambio significativo que deba
   * reportarse de inmediato al Shadow (reporte por evento).
   */
  virtual bool update(unsigned long nowMs) = 0;

  /** Escribe sus atributos dentro de state.reported. */
  virtual void report(JsonObject reported) const = 0;
};
