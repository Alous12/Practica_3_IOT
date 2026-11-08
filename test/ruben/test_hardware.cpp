// Prueba del hardware (Ruben): filtro del PIR y calibración del servo.
// Sin ESP32: usa los mismos stubs de test/luciana. Ver test/ruben/README.md.
#include <cassert>
#include <ctime>
#include <iostream>
#include "Arduino.h"
#include "sensors/PirSensor.h"
#include "actuators/DoorLock.h"

unsigned long fakeMillis = 0;
int fakeLevel = 0, servoAngle = -1;
bool servoAttached = false;
SerialMock Serial;

extern "C" time_t time(time_t *out) {
  const time_t now = 1800000000;
  if (out) *out = now;
  return now;
}

int main() {
  // --- PIR con filtro de 50 ms (valor por defecto) ---
  fakeMillis = 0; fakeLevel = 0;
  PirSensor pir(27, 1000);  // calentamiento corto para la prueba
  pir.begin();

  // Durante el calentamiento no se cuenta nada aunque OUT esté en alto.
  fakeLevel = 1;
  assert(!pir.update(500));
  JsonDocument s; pir.report(s.to<JsonObject>());
  assert(!s["sensor_listo"].as<bool>() && !s["movimiento"].as<bool>());
  assert(s["detecciones"].as<int>() == 0);

  // Fin del calentamiento: se reporta sensor_listo, pero el alto aún no cumple 50 ms.
  assert(pir.update(1000));
  assert(!pir.motion());
  assert(!pir.update(1049));
  assert(pir.update(1050));  // 50 ms estable -> movimiento
  assert(pir.motion());

  // Pulso de ruido de 20 ms en bajo: se ignora, sigue habiendo movimiento.
  fakeLevel = 0; assert(!pir.update(2000));
  fakeLevel = 1; assert(!pir.update(2020));
  assert(!pir.update(2100) && pir.motion());

  // Bajada real (estable 50 ms) y nueva subida: dos detecciones en total.
  fakeLevel = 0; assert(!pir.update(3000)); assert(pir.update(3050)); assert(!pir.motion());
  fakeLevel = 1; assert(!pir.update(6000)); assert(pir.update(6050));
  pir.report(s.as<JsonObject>());
  assert(s["detecciones"].as<int>() == 2);
  assert(s["ultima_deteccion"].as<uint32_t>() == 1800000000);

  // Pico de ruido en alto de 10 ms con sala vacía: no es detección.
  fakeLevel = 0; pir.update(9000); pir.update(9050);
  fakeLevel = 1; assert(!pir.update(9100));
  fakeLevel = 0; assert(!pir.update(9110)); assert(!pir.update(9200));
  pir.report(s.as<JsonObject>());
  assert(s["detecciones"].as<int>() == 2);

  // --- Calibración del servo: mueve, no cambia el estado y se suelta tras settleMs ---
  fakeMillis = 100;
  DoorLock door(13, 90, 0, 700);
  door.begin();
  door.loop(800); assert(!servoAttached);
  fakeMillis = 1000; door.calibrate(75);
  assert(servoAttached && servoAngle == 75 && door.isClosed());
  door.calibrate(200); assert(servoAngle == 180);
  door.calibrate(-5);  assert(servoAngle == 0);
  door.loop(1699); assert(servoAttached);
  door.loop(1700); assert(!servoAttached);

  std::cout << "OK: filtro del PIR (calentamiento, 50 ms, ruido alto/bajo) y calibracion del servo.\n";
}
