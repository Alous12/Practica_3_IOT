/**
 * Integración y comunicación de Luciana: WiFi, MQTT/TLS y Shadow.
 * esp32dev: prueba LOCAL por serie; NO se conecta a AWS ni usa Alexa.
 * esp32dev-aws: requiere los archivos net/ y secrets.h de comunicación de Luciana.
 */
#include <Arduino.h>
#include <esp_system.h>
#include "actuators/DoorLock.h"
#include "app/SmartObject.h"
#include "config.h"
#include "sensors/PirSensor.h"

#ifndef FIRMWARE_LOCAL_TEST
#error "Seleccione un entorno de platformio.ini."
#endif

#if FIRMWARE_LOCAL_TEST
namespace {
/** Transporte de diagnóstico LOCAL: JSON por USB; no representa AWS (RF2/RF3).
 * a/c generan un delta de prueba, solo tras una orden explícita del operador.
 */
class LocalShadowPort : public ShadowPort {
 public:
  bool connected() override { return true; }
  bool publishReported(JsonObjectConst reported) override {
    JsonDocument doc;
    doc["state"]["reported"] = reported;
    Serial.printf("[LOCAL t_ms=%lu] ", millis());
    serializeJson(doc, Serial);
    Serial.println();
    return true;
  }
  void onDelta(DeltaHandler handler) override { delta_ = handler; }
  void onConnected(ConnectedHandler handler) override { connected_ = handler; }
  void begin() { if (connected_) connected_(); }
  void loop() {
    // Una orden por iteración para no acumular trabajo bloqueante.
    if (!Serial.available()) return;
    const char command = Serial.read();
    if (command != 'a' && command != 'c') return;
    JsonDocument doc;
    doc[KEY_DOOR] = command == 'a' ? DOOR_OPEN : DOOR_CLOSED;
    if (delta_) delta_(doc.as<JsonObjectConst>());
  }
 private:
  DeltaHandler delta_;
  ConnectedHandler connected_;
};
LocalShadowPort channel;
}  // namespace
#else
#if !__has_include("net/ShadowClient.h") || !__has_include("net/WifiConnection.h") || !__has_include("net/TimeSync.h") || !__has_include("secrets.h")
#error "Complete include/secrets.h desde secrets.example.h para compilar la demo AWS."
#endif
#include "net/ShadowClient.h"
#include "net/WifiConnection.h"
#include "net/TimeSync.h"
#include "secrets.h"
namespace {
WifiConnection wifi(WIFI_SSID, WIFI_PASSWORD, WIFI_RETRY_MS);
ShadowClient shadow(AWS_IOT_ENDPOINT, MQTT_PORT, THING_NAME, AWS_ROOT_CA,
                    AWS_DEVICE_CERT, AWS_PRIVATE_KEY, MQTT_RETRY_MS);
/** Adapta la API del código base anterior, sin modificar net/. */
class AwsShadowPort : public ShadowPort {
 public:
  bool connected() override { return shadow.connected(); }
  bool publishReported(JsonObjectConst value) override { return shadow.publishReported(value); }
  void onDelta(DeltaHandler handler) override { shadow.onDelta(handler); }
  void onConnected(ConnectedHandler handler) override { shadow.onConnected(handler); }
};
AwsShadowPort channel;
}  // namespace
#endif

namespace {
PirSensor pir(PIR_PIN, PIR_WARMUP_MS);
DoorLock door(SERVO_PIN, SERVO_ANGLE_CLOSED, SERVO_ANGLE_OPEN, SERVO_SETTLE_MS);
SmartObject smartObject(channel, REPORT_MIN_GAP_MS, REPORT_PERIOD_MS);
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);
  Serial.printf("\n[Vigilante] Reinicio: %d\n", static_cast<int>(esp_reset_reason()));
  smartObject.addSensor(&pir);
  smartObject.addActuator(&door);
  smartObject.begin();
#if FIRMWARE_LOCAL_TEST
  Serial.println("[LOCAL] Sin AWS ni Alexa. a=abrir; c=cerrar. PIR: esperar 60 s.");
  channel.begin();
#else
  Serial.printf("[AWS] Thing: %s\n", THING_NAME);
  wifi.begin();
  shadow.begin(MQTT_BUFFER_SIZE);
#endif
}

void loop() {
#if FIRMWARE_LOCAL_TEST
  channel.loop();
#else
  const unsigned long now = millis();
  const bool wifiOk = wifi.ensure(now);
  if (wifi.justConnected()) {
    TimeSync::begin();
    shadow.retryNow();
  }
  if (wifiOk && shadow.ensure(now)) shadow.loop();
#endif
  // Tomar la hora después de red/comandos: no pasar un tiempo anterior al servo.
  smartObject.loop(millis());
}
