#pragma once

#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>

#include <functional>

/**
 * Cliente MQTT sobre TLS (puerto 8883) para el Device Shadow clásico del Thing.
 *
 * Tópicos usados ($aws/things/<thing>/shadow/...):
 *  - publica  update           -> estado reportado
 *  - publica  get              -> pide el documento completo al (re)conectarse
 *  - suscribe update/delta     -> cambios de desired que difieren de reported
 *  - suscribe get/accepted     -> respuesta a get (incluye "delta" si hay pendientes)
 */
class ShadowClient {
 public:
  /** Recibe el objeto con los atributos deseados pendientes (sección delta). */
  using DeltaHandler = std::function<void(JsonObjectConst delta)>;
  /** Se llama cada vez que la sesión MQTT se (re)establece. */
  using ConnectedHandler = std::function<void()>;

  ShadowClient(const char *endpoint, uint16_t port, const char *thingName, const char *rootCa,
               const char *deviceCert, const char *privateKey, unsigned long retryMs);

  void begin(uint16_t bufferSize);
  void onDelta(DeltaHandler handler) { deltaHandler_ = handler; }
  void onConnected(ConnectedHandler handler) { connectedHandler_ = handler; }

  /** Mantiene la sesión MQTT. Devuelve true si está conectado. */
  bool ensure(unsigned long nowMs);
  void loop();
  bool connected();

  /** Publica {"state":{"reported": <reported>}} en el tópico update. */
  bool publishReported(JsonObjectConst reported);

  /** Fuerza un intento de conexión inmediato (p. ej. al volver el WiFi). */
  void retryNow() { lastAttemptMs_ = 0; attempted_ = false; }

 private:
  void handleMessage(char *topic, byte *payload, unsigned int length);
  void requestDocument();

  WiFiClientSecure tls_;
  PubSubClient mqtt_;
  const char *endpoint_;
  uint16_t port_;
  const char *thingName_;
  const char *rootCa_;
  const char *deviceCert_;
  const char *privateKey_;
  unsigned long retryMs_;
  unsigned long lastAttemptMs_ = 0;
  bool attempted_ = false;

  String topicUpdate_;
  String topicDelta_;
  String topicGet_;
  String topicGetAccepted_;

  DeltaHandler deltaHandler_;
  ConnectedHandler connectedHandler_;
};
