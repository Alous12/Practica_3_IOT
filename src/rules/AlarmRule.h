#pragma once

#include "core/ControlRule.h"

class PirSensor;
class Buzzer;

/** Alarma local: intrusiones en bloqueo y apagado a los 30 s en cualquier modo. */
class AlarmRule : public ControlRule {
 public:
  AlarmRule(const PirSensor &pir, Buzzer &buzzer) : pir_(pir), buzzer_(buzzer) {}
  bool evaluate(JsonObjectConst reported) override;
  void clearDesired(JsonObject desired) const override;

 private:
  const PirSensor &pir_;
  Buzzer &buzzer_;
};
