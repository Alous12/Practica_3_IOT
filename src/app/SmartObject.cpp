#include "app/SmartObject.h"

#include <WiFi.h>

#include "config.h"

namespace {
// Límite del texto de "origen": un valor enorme haría que reported no quepa en el
// búfer de publicación y el dispositivo dejaría de reportar.
constexpr size_t ORIGIN_MAX_LEN = 16;
}  // namespace

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

  // Antes del guard de red: el cierre local funciona sin WiFi/MQTT.
  if (!rules_.empty()) {
    JsonDocument snapshot;
    collectState(snapshot.to<JsonObject>(), nowMs);
    for (ControlRule *rule : rules_) {
      if (rule->evaluate(snapshot.as<JsonObjectConst>())) {
        origin_ = ORIGIN_EDGE;
        rule->clearDesired(pendingDesired_.as<JsonObject>().isNull()
                               ? pendingDesired_.to<JsonObject>()
                               : pendingDesired_.as<JsonObject>());
        reportPending_ = true;
        forceReport_ = true;
        collectState(snapshot.to<JsonObject>(), nowMs);
      }
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
    // Al reconectar puede llegar el get/accepted con una apertura anterior.
    // El cierre local tiene prioridad hasta enviar la limpieza pendiente.
    if (!pendingDesired_.as<JsonObjectConst>()[actuator->key()].isUnbound()) continue;
    JsonVariantConst value = delta[actuator->key()];
    if (!value.isNull() && actuator->applyDesired(value)) {
      changed = true;
    }
  }
  for (Setting *setting : settings_) {
    JsonVariantConst value = delta[setting->key()];
    if (!value.isNull() && setting->applyDesired(value)) {
      changed = true;  // un parámetro cambió: confirmarlo en reported de inmediato
    }
  }

  // Origen del cambio: se copia tal cual llega (voz, edge, nube...).
  // Si una regla local está limpiando "origen", un delta antiguo no pisa el "edge".
  JsonVariantConst origin = delta[KEY_ORIGIN];
  const bool originPending = !pendingDesired_.as<JsonObjectConst>()[KEY_ORIGIN].isUnbound();
  if (!origin.isNull() && !originPending) {
    const char *text = origin.is<const char *>() ? origin.as<const char *>() : nullptr;
    if (text == nullptr || text[0] == '\0' || strlen(text) > ORIGIN_MAX_LEN) {
      Serial.println("[Origen] Valor deseado inválido (se espera texto corto)");
    } else if (strcmp(origin_.c_str(), text) != 0) {
      origin_ = text;  // String copia el texto: el búfer JSON se libera tras el delta
      Serial.printf("[Origen] %s\n", origin_.c_str());
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
  collectState(reported, nowMs);

  if (shadow_.publishUpdate(reported, pendingDesired_.as<JsonObjectConst>())) {
    pendingDesired_.clear();
    reportPending_ = false;
    forceReport_ = false;
    lastReportMs_ = nowMs;
  }
}

void SmartObject::collectState(JsonObject reported, unsigned long nowMs) const {
  for (Sensor *sensor : sensors_) {
    sensor->report(reported);
  }
  for (Actuator *actuator : actuators_) {
    actuator->report(reported);
  }
  for (Setting *setting : settings_) {
    setting->report(reported);
  }
  reported[KEY_ORIGIN] = origin_.c_str();  // ArduinoJson copia el texto
  reported[KEY_UPTIME] = nowMs / 1000;
  reported[KEY_RSSI] = WiFi.RSSI();
}
