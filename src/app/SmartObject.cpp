#include "app/SmartObject.h"

#include <WiFi.h>

#include "config.h"

SmartObject::SmartObject(ShadowPort &shadow, unsigned long minGapMs, unsigned long periodMs)
    : shadow_(shadow), minGapMs_(minGapMs), periodMs_(periodMs) {}

void SmartObject::begin() {
  for (Sensor *sensor : sensors_) {
    sensor->begin();
  }
  for (Actuator *actuator : actuators_) {
    actuator->begin();
  }
  shadow_.onDelta([this](JsonObjectConst delta) { handleDelta(delta); });
  shadow_.onConnected([this]() {
    reportPending_ = true;
    forceReport_ = true;  // publicar el estado completo incluso al inicio del MCU
  });
}

void SmartObject::loop(unsigned long nowMs) {
  for (Actuator *actuator : actuators_) {
    actuator->loop(nowMs);
  }
  for (Sensor *sensor : sensors_) {
    if (sensor->update(nowMs)) {
      reportPending_ = true;  // reporte por evento
    }
  }

  if (!shadow_.connected()) {
    return;  // el estado se publicará completo al reconectarse
  }

  bool periodic = nowMs - lastReportMs_ >= periodMs_;
  bool eventReady = reportPending_ &&
                    (forceReport_ || nowMs - lastReportMs_ >= minGapMs_);
  if (periodic || eventReady) {
    publishState(nowMs);
  }
}

void SmartObject::handleDelta(JsonObjectConst delta) {
  bool changed = false;
  for (Actuator *actuator : actuators_) {
    JsonVariantConst value = delta[actuator->key()];
    if (!value.isNull() && actuator->applyDesired(value)) {
      changed = true;
    }
  }
  if (changed) {
    reportPending_ = true;
    forceReport_ = true;  // no falsear lastReportMs_: evitar errores al desbordar millis()
  }
}

void SmartObject::publishState(unsigned long nowMs) {
  JsonDocument doc;
  JsonObject reported = doc.to<JsonObject>();
  for (Sensor *sensor : sensors_) {
    sensor->report(reported);
  }
  for (Actuator *actuator : actuators_) {
    actuator->report(reported);
  }
  reported[KEY_UPTIME] = nowMs / 1000;
  reported[KEY_RSSI] = WiFi.RSSI();

  if (shadow_.publishReported(reported)) {
    reportPending_ = false;
    forceReport_ = false;
    lastReportMs_ = nowMs;
  }
}
