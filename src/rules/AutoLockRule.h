#pragma once

#include "core/ControlRule.h"
#include "sensors/PirSensor.h"
#include "actuators/DoorLock.h"

/** RF13: cerrar ante un flanco nuevo en automatico o bloqueo. */
class AutoLockRule : public ControlRule {
 public:
  AutoLockRule(const PirSensor &pir, DoorLock &door) : pir_(pir), door_(door) {}
  bool evaluate(JsonObjectConst reported) override;
  void clearDesired(JsonObject desired) const override;

 private:
  const PirSensor &pir_;
  DoorLock &door_;
};
