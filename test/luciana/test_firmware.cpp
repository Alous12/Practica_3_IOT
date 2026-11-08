#include <cassert>
#include <climits>
#include <iostream>
#include "Arduino.h"
#include "WiFi.h"
#include "sensors/PirSensor.h"
#include "actuators/DoorLock.h"
#include "app/SmartObject.h"
#include "net/ShadowClient.h"
#include <ctime>
unsigned long fakeMillis=0;
int fakeLevel=0, servoAngle=-1;
bool servoAttached=false;
SerialMock Serial;
WiFiMock WiFi;
// Hora de prueba controlada, sin NTP ni red.
extern "C" time_t time(time_t *out) {
  const time_t now=1800000000;
  if (out) *out=now;
  return now;
}
int main() {
  // El calentamiento empieza al inicializar el sensor, no al encender el MCU.
  // debounce=0: esta prueba avanza de a 1 ms; el filtro se prueba en test/ruben/.
  fakeMillis=10000; PirSensor pir(27,60000,0); pir.begin();
  assert(!pir.update(60000));
  fakeLevel=1; assert(pir.update(70000));
  JsonDocument state; pir.report(state.to<JsonObject>());
  assert(state["sensor_listo"].as<bool>());
  assert(state["movimiento"].as<bool>());
  assert(state["detecciones"].as<int>()==1);
  assert(state["ultima_deteccion"].as<uint32_t>()==1800000000);
  assert(!pir.update(70001));
  fakeLevel=0; assert(pir.update(70002));
  fakeLevel=1; assert(pir.update(70003));
  pir.report(state.as<JsonObject>()); assert(state["detecciones"].as<int>()==2);
  fakeMillis=ULONG_MAX-100; pir.begin();
  assert(!pir.update(100));
  assert(pir.update(60000)); // calentamiento atraviesa el desborde

  // Tipos/valores inválidos no mueven el servo; detach respeta 700 ms.
  fakeMillis=100; DoorLock door(13,90,0,700); door.begin();
  assert(servoAngle==90 && servoAttached);
  JsonDocument value;
  value.set(90); assert(!door.applyDesired(value.as<JsonVariantConst>()));
  value.set("incorrecta"); assert(!door.applyDesired(value.as<JsonVariantConst>()));
  value.set("abierta"); assert(door.applyDesired(value.as<JsonVariantConst>()));
  assert(servoAngle==0 && !door.isClosed());
  door.loop(799); assert(servoAttached);
  door.loop(800); assert(!servoAttached);

  // Reporte inicial, evento, latido, fallo de publicación y reconexión.
  ShadowClient shadow; SmartObject obj(shadow,500,60000);
  obj.addSensor(&pir); obj.addActuator(&door);
  fakeMillis=1000; fakeLevel=0; obj.begin();
  obj.loop(1000); assert(shadow.reports==0);
  shadow.online=true; shadow.connect(); obj.loop(1000);
  assert(shadow.reports==1);
  obj.loop(60999); assert(shadow.reports==1);
  obj.loop(61000); assert(shadow.reports==2);
  fakeLevel=1; obj.loop(61100); assert(shadow.reports==2);
  obj.loop(61500); assert(shadow.reports==3);
  shadow.publishOk=false;
  value.clear(); value["puerta"]="abierta";
  fakeMillis=61501; shadow.delta(value.as<JsonObjectConst>());
  obj.loop(61501); assert(shadow.reports==3);
  shadow.publishOk=true; obj.loop(61502); assert(shadow.reports==4);
  assert(shadow.last["puerta"].as<const char*>()==std::string("abierta"));
  shadow.online=false; obj.loop(70000); assert(shadow.reports==4);
  shadow.online=true; shadow.connect(); obj.loop(70001); assert(shadow.reports==5);
  std::cout << "OK: PIR, servo y reportes: calentamiento, flancos, desborde, "
               "validacion, PWM, eventos, latido, reintento y reconexion simulada.\n";
}
