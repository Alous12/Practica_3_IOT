#pragma once

#include <Arduino.h>

#include <vector>

#include "config.h"
#include "core/Actuator.h"
#include "core/Sensor.h"
#include "core/Setting.h"
#include "core/ShadowPort.h"
#include "core/ControlRule.h"

/**
 * Requerimientos: RF2: reportar eventos y latidos; RF3: distribuir y confirmar órdenes.
 *
 * Orquestador del objeto inteligente.
 *
 * - Lee los sensores y publica el estado en state.reported:
 *     · por evento (cambio detectado), con separación mínima REPORT_MIN_GAP_MS;
 *     · periódicamente cada REPORT_PERIOD_MS como respaldo.
 * - Recibe los deltas del Shadow y los reparte al actuador o parámetro (Setting)
 *   dueño de cada clave; guarda además el origen del cambio ("origen").
 * - Tras aplicar un delta, confirma el nuevo estado en reported.
 * - Evalúa las reglas locales (ControlRule) aun sin red; si una actúa, el origen
 *   pasa a "edge" y se limpia en desired lo que la regla indique.
 *
 * No conoce sensores, actuadores, parámetros ni reglas concretos: trabaja con las
 * interfaces Sensor, Actuator, Setting y ControlRule, de modo que se pueden agregar más
 * sin rediseñar.
 */
class SmartObject {
 public:
  SmartObject(ShadowPort &shadow, unsigned long minGapMs, unsigned long periodMs);

  void addSensor(Sensor *sensor) { sensors_.push_back(sensor); }
  void addActuator(Actuator *actuator) { actuators_.push_back(actuator); }
  void addSetting(Setting *setting) { settings_.push_back(setting); }
  void addRule(ControlRule *rule) { rules_.push_back(rule); }

  void begin();
  void loop(unsigned long nowMs);

 private:
  void handleDelta(JsonObjectConst delta);
  void publishState(unsigned long nowMs);
  void collectState(JsonObject reported, unsigned long nowMs) const;

  ShadowPort &shadow_;
  std::vector<Sensor *> sensors_;
  std::vector<Actuator *> actuators_;
  std::vector<Setting *> settings_;
  std::vector<ControlRule *> rules_;
  JsonDocument pendingDesired_;  // atributos de desired a limpiar tras una acción local
  String origin_ = ORIGIN_BOOT;  // quién hizo el último cambio (KEY_ORIGIN)
  unsigned long minGapMs_;
  unsigned long periodMs_;
  unsigned long lastReportMs_ = 0;
  bool forceReport_ = false;  // confirmación sin alterar el reloj del latido
  bool reportPending_ = true;  // publicar el estado completo al conectarse
};
