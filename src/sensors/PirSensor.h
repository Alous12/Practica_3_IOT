#pragma once

#include "core/Sensor.h"

/**
 * Sensor de movimiento PIR HC-SR501.
 *
 * Capa: hardware (Ruben). Requerimientos: RF1 detectar movimiento; RF2 exponer la lectura.
 *
 * Reporta en state.reported:
 *  - movimiento:        true mientras la salida filtrada del PIR está en alto.
 *  - detecciones:       flancos de subida desde begin(); no cuenta el calentamiento.
 *  - ultima_deteccion:  hora UTC (epoch, s) del último flanco; 0 si aún no hay hora NTP.
 *  - sensor_listo:      false durante el calentamiento del módulo (~60 s).
 *
 * Ajustes físicos del módulo: jumper en H (disparo repetible), Tx al mínimo (~3 s),
 * Sx al medio. OUT entrega 3,3 V y va directo al GPIO, sin divisor.
 */
class PirSensor : public Sensor {
 public:
  /**
   * @param pin        GPIO conectado a OUT del HC-SR501.
   * @param warmupMs   Calentamiento tras begin(); mientras dura no se reporta movimiento.
   * @param debounceMs Tiempo que un nivel debe mantenerse estable para aceptarse.
   *                   Descarta pulsos cortos (ruido del servo). 0 = sin filtro.
   */
  PirSensor(uint8_t pin, unsigned long warmupMs, unsigned long debounceMs = 50);

  void begin() override;
  bool update(unsigned long nowMs) override;
  void report(JsonObject reported) const override;

  bool motion() const { return motion_; }

 private:
  uint8_t pin_;
  unsigned long warmupMs_;
  unsigned long debounceMs_;
  unsigned long startedMs_ = 0;  // inicio del calentamiento, no del MCU
  bool ready_ = false;
  bool motion_ = false;          // estado filtrado (lo que se reporta)
  bool rawLevel_ = false;        // última lectura cruda del pin
  unsigned long rawSinceMs_ = 0; // desde cuándo la lectura cruda no cambia
  uint32_t detections_ = 0;
  uint32_t lastDetectionEpoch_ = 0;
};
