#pragma once

#include <ArduinoJson.h>

/**
 * Requerimientos: RF3 (aplicar desired) y RF2 (reporte).
 *
 * Interfaz común de todos los actuadores controlados desde el Shadow.
 *
 * Cada actuador es dueño de UNA clave del documento (key()). Cuando llega un
 * delta con esa clave, SmartObject llama a applyDesired(). Para agregar el
 * buzzer en una entrega futura basta con heredar de esta clase y registrarlo
 * con SmartObject::addActuator().
 */
class Actuator {
 public:
  virtual ~Actuator() = default;

  /** Nombre del atributo del Shadow que controla (p. ej. "puerta"). */
  virtual const char *key() const = 0;

  /** Configura pines y deja el actuador en su estado seguro inicial. */
  virtual void begin() = 0;

  /** Tareas no bloqueantes (p. ej. soltar el servo al terminar de moverse). */
  virtual void loop(unsigned long nowMs) = 0;

  /**
 * Requerimientos: RF3 (aplicar desired) y RF2 (reporte).
 *
   * Aplica el valor deseado recibido en el delta.
   * Devuelve false si el valor no es válido (se ignora y se registra en el log).
   */
  virtual bool applyDesired(JsonVariantConst value) = 0;

  /** Escribe su estado actual dentro de state.reported. */
  virtual void report(JsonObject reported) const = 0;
};
