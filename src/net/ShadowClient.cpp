#include "net/ShadowClient.h"

#include "net/TimeSync.h"

ShadowClient::ShadowClient(const char *endpoint, uint16_t port, const char *thingName,
                           const char *rootCa, const char *deviceCert, const char *privateKey,
                           unsigned long retryMs)
    : mqtt_(tls_),
      endpoint_(endpoint),
      port_(port),
      thingName_(thingName),
      rootCa_(rootCa),
      deviceCert_(deviceCert),
      privateKey_(privateKey),
      retryMs_(retryMs) {
  String base = String("$aws/things/") + thingName_ + "/shadow/";
  topicUpdate_ = base + "update";
  topicDelta_ = base + "update/delta";
  topicGet_ = base + "get";
  topicGetAccepted_ = base + "get/accepted";
}

void ShadowClient::begin(uint16_t bufferSize) {
  tls_.setCACert(rootCa_);
  tls_.setCertificate(deviceCert_);
  tls_.setPrivateKey(privateKey_);

  mqtt_.setServer(endpoint_, port_);
  mqtt_.setBufferSize(bufferSize);
  mqtt_.setKeepAlive(30);
  mqtt_.setCallback([this](char *topic, byte *payload, unsigned int length) {
    handleMessage(topic, payload, length);
  });
}

bool ShadowClient::connected() { return mqtt_.connected(); }

void ShadowClient::loop() { mqtt_.loop(); }

bool ShadowClient::ensure(unsigned long nowMs) {
  if (mqtt_.connected()) {
    return true;
  }
  if (attempted_ && nowMs - lastAttemptMs_ < retryMs_) {
    return false;
  }
  attempted_ = true;
  lastAttemptMs_ = nowMs;

  Serial.printf("[MQTT] Conectando a %s:%u como %s...\n", endpoint_, port_, thingName_);
  // El client ID DEBE ser el nombre del Thing: la política de IoT lo exige
  // mediante la variable ${iot:Connection.Thing.ThingName}.
  if (!mqtt_.connect(thingName_)) {
    Serial.printf("[MQTT] Falló (estado %d). Reintento en %lu ms\n", mqtt_.state(), retryMs_);
    return false;
  }

  Serial.println("[MQTT] Conectado");
  mqtt_.subscribe(topicDelta_.c_str(), 1);
  mqtt_.subscribe(topicGetAccepted_.c_str(), 1);
  if (connectedHandler_) {
    connectedHandler_();
  }
  // Sincronización tras (re)conectar: pedir el documento para aplicar
  // cualquier "desired" que haya quedado pendiente mientras no había conexión.
  requestDocument();
  return true;
}

bool ShadowClient::publishReported(JsonObjectConst reported) {
  if (!mqtt_.connected()) {
    return false;
  }
  JsonDocument doc;
  doc["state"]["reported"] = reported;

  char buffer[512];
  size_t len = serializeJson(doc, buffer, sizeof(buffer));
  bool ok = mqtt_.publish(topicUpdate_.c_str(), reinterpret_cast<const uint8_t *>(buffer), len);
  Serial.printf("[Shadow] reported %s %s\n", ok ? "->" : "FALLÓ", buffer);
  return ok;
}

void ShadowClient::requestDocument() {
  mqtt_.publish(topicGet_.c_str(), "{}");
  Serial.println("[Shadow] Solicitando documento (get) para sincronizar");
}

void ShadowClient::handleMessage(char *topic, byte *payload, unsigned int length) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.printf("[Shadow] JSON inválido en %s: %s\n", topic, err.c_str());
    return;
  }

  JsonObjectConst delta;
  if (topicDelta_ == topic) {
    // update/delta: {"state": {<atributos deseados que difieren>}, ...}
    delta = doc["state"].as<JsonObjectConst>();
  } else if (topicGetAccepted_ == topic) {
    // get/accepted: {"state": {"desired":..., "reported":..., "delta": {...}}}
    delta = doc["state"]["delta"].as<JsonObjectConst>();
    if (delta.isNull()) {
      Serial.println("[Shadow] Documento sincronizado, sin cambios pendientes");
      return;
    }
  } else {
    return;
  }

  // epoch_ms permite medir la latencia Lambda -> dispositivo comparando con CloudWatch.
  unsigned long long epochMs = TimeSync::nowEpochMs();
  Serial.printf("[Shadow] delta recibido epoch_ms=%llu (%s)\n", epochMs, topic);
  if (deltaHandler_ && !delta.isNull()) {
    deltaHandler_(delta);
  }
}
