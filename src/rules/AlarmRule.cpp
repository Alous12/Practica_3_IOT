#include "rules/AlarmRule.h"

// En las pruebas (test/luciana/run.ps1) "actuators/Buzzer.h" resuelve al doble de
// test/luciana/alarm_stubs/, que se incluye antes que src/.
#include <Arduino.h>
#include <cstring>

#include "actuators/Buzzer.h"
#include "config.h"
#include "sensors/PirSensor.h"

bool AlarmRule::evaluate(JsonObjectConst reported) {
  // Primero vence el tiempo: ni un nuevo pulso ni el origen voz/nube lo renuevan.
  // La resta unsigned tambien funciona al desbordarse millis().
  if (buzzer_.isOn()) {
    if (millis() - buzzer_.onSinceMs() >= ALARM_MAX_MS) {
      buzzer_.turnOff();
      return true;
    }
    return false;
  }

  const char *mode = reported[KEY_MODE] | MODE_MANUAL;
  if (strcmp(mode, MODE_LOCKDOWN) == 0 && pir_.motionStarted()) {
    buzzer_.turnOn();
    return true;
  }
  return false;
}

void AlarmRule::clearDesired(JsonObject desired) const {
  // No reconstruir el objeto: puede contener la limpieza de AutoLockRule.
  desired[KEY_ALARM] = nullptr;
  desired[KEY_ORIGIN] = nullptr;
}
