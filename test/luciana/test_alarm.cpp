#include <cassert>
#include <climits>
#include <iostream>
#include <string>
#include "Arduino.h"
#include "WiFi.h"
#include "config.h"
#include "actuators/Buzzer.h"
#include "actuators/DoorLock.h"
#include "app/SmartObject.h"
#include "net/ShadowClient.h"
#include "rules/AlarmRule.h"
#include "rules/AutoLockRule.h"
#include "settings/OperatingMode.h"

unsigned long fakeMillis = 0;
int fakeLevel = 0, servoAngle = -1;
bool servoAttached = false;
SerialMock Serial;
WiFiMock WiFi;

void testRule() {
  PirSensor pir(27, 60, 50);
  Buzzer buzzer;
  AlarmRule rule(pir, buzzer);
  JsonDocument state;
  state[KEY_MODE] = MODE_LOCKDOWN;
  fakeMillis = 0; fakeLevel = 0;
  pir.begin(); buzzer.begin();
  auto step = [&](unsigned long now, int level) {
    fakeMillis = now; fakeLevel = level; pir.update(now);
    return rule.evaluate(state.as<JsonObjectConst>());
  };
  assert(!step(10, 1)); // calentamiento
  assert(!step(60, 1));
  assert(!step(109, 1)); // filtro de 50 ms
  assert(step(110, 1) && buzzer.isOn());
  assert(buzzer.onSinceMs() == 110 && buzzer.onCalls == 1);
  assert(!step(111, 1)); // alto sostenido no dispara de nuevo
  step(120, 0); step(170, 0); step(180, 1);
  assert(!step(230, 1)); // nuevo flanco mientras suena: no reinicia tiempo
  assert(buzzer.onSinceMs() == 110 && buzzer.onCalls == 1);
  assert(!step(30109, 1) && buzzer.isOn());
  assert(step(30110, 1) && !buzzer.isOn()); // exactamente 30 segundos
  assert(!step(30111, 1)); // no revive por mantener el PIR alto
  step(30200, 0); step(30250, 0); step(30300, 1);
  assert(step(30350, 1) && buzzer.isOn()); // nuevo ciclo con otro flanco

  for (const char *mode : {MODE_MANUAL, MODE_AUTO, "desconocido"}) {
    state[KEY_MODE] = mode;
    buzzer.turnOff();
    pir.begin();
    const unsigned long start = fakeMillis;
    assert(!step(start + 100, 0));
    step(start + 200, 1);
    assert(!step(start + 250, 1) && !buzzer.isOn());
  }
  // Voz y nube usan el mismo reloj del actuador, incluso en manual.
  for (const char *origin : {ORIGIN_VOICE, ORIGIN_CLOUD}) {
    state[KEY_MODE] = MODE_MANUAL;
    state[KEY_ORIGIN] = origin;
    fakeMillis = 50000;
    buzzer.turnOn();
    assert(!step(79999, 0));
    assert(step(80000, 0) && !buzzer.isOn());
  }
  // Un flanco justo al vencimiento no vuelve a encenderla en el mismo ciclo.
  state[KEY_MODE] = MODE_LOCKDOWN;
  fakeMillis = 90000; fakeLevel = 0; pir.begin(); buzzer.turnOn();
  step(90100, 0); step(119950, 1);
  assert(step(120000, 1) && !buzzer.isOn());
  assert(buzzer.onSinceMs() == 90000);
  assert(!step(120001, 1));
  // Cruce del desborde de millis().
  fakeMillis = ULONG_MAX - 100;
  buzzer.turnOn();
  assert(!step(29898, 0) && buzzer.isOn());
  assert(step(29899, 0) && !buzzer.isOn());

  JsonDocument cleanup;
  cleanup[KEY_DOOR] = nullptr;
  rule.clearDesired(cleanup.as<JsonObject>());
  assert(cleanup.size() == 3); // no borra puerta de la otra regla
  for (const char *key : {KEY_ALARM, KEY_ORIGIN, KEY_DOOR}) {
    assert(!cleanup[key].isUnbound() && cleanup[key].isNull());
  }
}

void testOfflineIntegration() {
  fakeMillis = 0; fakeLevel = 0;
  PirSensor pir(27, 0, 0);
  DoorLock door(25, 90, 0, 700);
  OperatingMode mode;
  Buzzer buzzer;
  AutoLockRule closeRule(pir, door);
  AlarmRule alarmRule(pir, buzzer);
  ShadowClient shadow;
  SmartObject object(shadow, 500, 60000);
  object.addSensor(&pir); object.addActuator(&door); object.addActuator(&buzzer);
  object.addSetting(&mode);
  object.addRule(&closeRule); object.addRule(&alarmRule);
  object.begin();
  JsonDocument command;
  command[KEY_MODE] = MODE_LOCKDOWN;
  command[KEY_DOOR] = DOOR_OPEN;
  command[KEY_ORIGIN] = ORIGIN_VOICE;
  shadow.delta(command.as<JsonObjectConst>());
  assert(!door.isClosed());
  auto step = [&](unsigned long now, int level) {
    fakeMillis = now; fakeLevel = level; object.loop(now);
  };
  step(100, 0); step(101, 1);
  assert(!shadow.online && door.isClosed() && buzzer.isOn());
  assert(shadow.attempts == 0); // ambas reglas actuaron sin transporte
  step(30100, 1); assert(buzzer.isOn());
  step(30101, 1); assert(!buzzer.isOn()); // apagado tambien sin red

  JsonDocument old;
  old[KEY_DOOR] = DOOR_OPEN;
  old[KEY_ALARM] = ALARM_ON;
  old[KEY_ORIGIN] = ORIGIN_CLOUD;
  shadow.online = true; shadow.connect();
  shadow.delta(old.as<JsonObjectConst>());
  assert(door.isClosed() && !buzzer.isOn());
  shadow.publishOk = false;
  step(30102, 1);
  assert(shadow.reports == 0);
  shadow.delta(old.as<JsonObjectConst>());
  assert(!buzzer.isOn()); // la limpieza sigue pendiente si falla publicar
  shadow.publishOk = true;
  step(30103, 1);
  assert(shadow.reports == 1);
  assert(std::string(shadow.last[KEY_ORIGIN].as<const char*>()) == ORIGIN_EDGE);
  assert(std::string(shadow.last[KEY_ALARM].as<const char*>()) == ALARM_OFF);
  assert(shadow.lastDesired.size() == 3);
  for (const char *key : {KEY_DOOR, KEY_ALARM, KEY_ORIGIN}) {
    assert(!shadow.lastDesired[key].isUnbound() && shadow.lastDesired[key].isNull());
  }
  assert(shadow.lastDesired[KEY_MODE].isUnbound()); // conserva ajustes

  // Comando real de nube con red: se apaga a los 30 s y reporta edge.
  JsonDocument cloud;
  cloud[KEY_ALARM] = ALARM_ON; cloud[KEY_ORIGIN] = ORIGIN_CLOUD;
  fakeMillis = 40000; shadow.delta(cloud.as<JsonObjectConst>());
  step(40000, 1); assert(buzzer.isOn());
  assert(std::string(shadow.last[KEY_ORIGIN].as<const char*>()) == ORIGIN_CLOUD);
  step(69999, 1); assert(buzzer.isOn());
  step(70000, 1); assert(!buzzer.isOn());
  assert(std::string(shadow.last[KEY_ORIGIN].as<const char*>()) == ORIGIN_EDGE);
}

int main() {
  testRule();
  testOfflineIntegration();
  std::cout << "OK AlarmRule: bloqueo, flancos, 30s, voz/nube, desborde, offline, "
               "reglas combinadas y limpieza ante delta antiguo. Buzzer simulado.\n";
}
