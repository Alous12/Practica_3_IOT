#pragma once

#include "core/Sensor.h"

/**
 * Requerimientos: RF1: detectar movimiento; RF2: exponer la lectura al reporte.
 *
 * Sensor de movimiento PIR HC-SR501.
 *
 * Reporta:
 *  - movimiento:        true mientras la salida del PIR está en alto.
 *  - detecciones:       número de flancos de subida desde el encendido.
 *  - ultima_deteccion:  hora UTC (epoch, s) del último flanco; 0 si aún no hay hora NTP.
 *  - sensor_listo:      false durante el tiempo de calentamiento del módulo.
 */
class PirSensor : public Sensor {
 public:
  PirSensor(uint8_t pin, unsigned long warmupMs);

  void begin() override;
  bool update(unsigned long nowMs) override;
  void report(JsonObject reported) const override;

  bool motion() const { return motion_; }

 private:
  uint8_t pin_;
  unsigned long warmupMs_;
  unsigned long startedMs_ = 0;  // inicio del calentamiento, no del MCU
  bool ready_ = false;
  bool motion_ = false;
  uint32_t detections_ = 0;
  uint32_t lastDetectionEpoch_ = 0;
};
