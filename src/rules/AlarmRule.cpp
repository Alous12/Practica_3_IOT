#include "rules/AlarmRule.h"

// Buzzer y sus constantes son el aporte de Alejandro. Hasta que se integren,
// el firmware existente sigue compilando; las pruebas usan un doble de Buzzer.
#if __has_include("actuators/Buzzer.h")
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
#endif
