#pragma once
#include <ArduinoJson.h>
#include <functional>

/** Contrato de integración de Luciana (RF2/RF3).
 * No implementa WiFi ni MQTT: la capa de comunicación de Luciana debe adaptar ShadowClient.
 * Las callbacks se ejecutan en el mismo hilo que el loop del firmware.
 */
class ShadowPort {
 public:
  using DeltaHandler = std::function<void(JsonObjectConst)>;
  using ConnectedHandler = std::function<void()>;
  virtual ~ShadowPort() = default;
  virtual bool connected() = 0;
  virtual bool publishReported(JsonObjectConst reported) = 0;
  virtual void onDelta(DeltaHandler handler) = 0;
  virtual void onConnected(ConnectedHandler handler) = 0;
};
