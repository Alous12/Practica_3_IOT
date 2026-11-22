#include <cassert>
#include <iostream>
#include "Arduino.h"
#include "WiFi.h"
#include "app/SmartObject.h"
#include "rules/AutoLockRule.h"
#include "net/ShadowClient.h"

unsigned long fakeMillis = 0;
int fakeLevel = 0, servoAngle = -1;
bool servoAttached = false;
SerialMock Serial;
WiFiMock WiFi;

// Doble del ajuste de Alejandro: no implementa su interfaz ni se carga al ESP32.
class ModeFixture : public Sensor {
 public:
  const char *value = "manual";
  void begin() override {}
  bool update(unsigned long) override { return false; }
  void report(JsonObject state) const override { state["modo"] = value; }
};

int main() {
  PirSensor pir(27, 60, 50);
  DoorLock door(25, 90, 0, 700);
  ModeFixture mode;
  AutoLockRule rule(pir, door);
  ShadowClient shadow;
  SmartObject object(shadow, 500, 60000);
  object.addSensor(&pir);
  object.addSensor(&mode);
  object.addActuator(&door);
  object.addRule(&rule);
  auto step = [&](unsigned long ms, int level) {
    fakeMillis = ms; fakeLevel = level; object.loop(ms);
  };
  auto open = [&]() {
    JsonDocument command;
    command["puerta"] = "abierta";
    command["origen"] = "voz";
    shadow.delta(command.as<JsonObjectConst>());
    assert(!door.isClosed());
  };
  object.begin();
  assert(door.isClosed() && servoAttached && servoAngle == 90);
  assert(!door.close());
  open();
  step(30, 1); assert(!pir.motionStarted() && !door.isClosed()); // calentamiento
  step(60, 1); step(109, 1);
  assert(!pir.motionStarted()); // filtro aun no cumplido
  step(110, 1);
  assert(pir.motionStarted() && !door.isClosed()); // manual: no actua
  mode.value = "automatico";
  step(111, 1);
  assert(!pir.motionStarted() && !door.isClosed()); // nivel alto != flanco nuevo
  step(120, 0); step(170, 0);
  step(180, 1); step(229, 1);
  assert(!door.isClosed());
  step(230, 1);
  assert(!shadow.online && pir.motionStarted() && door.isClosed());
  assert(shadow.attempts == 0 && servoAngle == 90); // cierre SIN red
  step(929, 1); assert(servoAttached);
  step(930, 1); assert(!servoAttached);
  assert(!door.close() && !servoAttached); // no reinicia PWM

  // get/accepted antiguo al reconectar no debe reabrir el cierre pendiente.
  JsonDocument old;
  old["puerta"] = "abierta"; old["origen"] = "voz";
  shadow.online = true;
  shadow.connect();
  shadow.delta(old.as<JsonObjectConst>());
  assert(door.isClosed());
  shadow.publishOk = false;
  step(931, 1); assert(shadow.reports == 0);
  shadow.delta(old.as<JsonObjectConst>());
  assert(door.isClosed()); // conserva limpieza ante un fallo de publicacion
  shadow.publishOk = true;
  step(932, 1);
  assert(shadow.reports == 1);
  assert(std::string(shadow.last["origen"].as<const char*>()) == "edge");
  assert(std::string(shadow.last["puerta"].as<const char*>()) == "cerrada");
  assert(shadow.lastDesired.size() == 2);
  assert(!shadow.lastDesired["puerta"].isUnbound());
  assert(shadow.lastDesired["puerta"].isNull());
  assert(shadow.lastDesired["origen"].isNull());
  assert(shadow.lastDesired["modo"].isUnbound()); // no borra ajustes

  mode.value = "bloqueo";
  open();
  step(940, 0); step(990, 0);
  const int beforeLockdown = shadow.reports;
  step(1000, 1); step(1050, 1);
  assert(door.isClosed() && shadow.reports == beforeLockdown + 1);
  // Nuevo pulso con puerta cerrada no causa otra accion ni reinicia PWM.
  step(1750, 1); assert(!servoAttached);
  step(1760, 0); step(1810, 0);
  step(1820, 1); step(1870, 1);
  assert(door.isClosed() && !servoAttached);

  mode.value = "desconocido";
  open();
  step(1880, 0); step(1930, 0);
  step(1940, 1); step(1990, 1);
  assert(!door.isClosed());
  std::cout << "OK Edge: manual/automatico/bloqueo, calentamiento, filtro, flanco, "
               "cierre sin red, PWM idempotente, delta antiguo, reintento y limpieza atomica.\n";
}
