#pragma once

/**
 * Mantiene la conexión WiFi sin bloquear el loop().
 * Si se pierde la red, reintenta cada WIFI_RETRY_MS.
 */
class WifiConnection {
 public:
  WifiConnection(const char *ssid, const char *password, unsigned long retryMs);

  void begin();

  /** Devuelve true si hay conexión; si no, reintenta cuando corresponde. */
  bool ensure(unsigned long nowMs);

  /** true solo en la iteración en que la conexión se (re)establece. */
  bool justConnected() const { return justConnected_; }

 private:
  const char *ssid_;
  const char *password_;
  unsigned long retryMs_;
  unsigned long lastAttemptMs_ = 0;
  bool attempted_ = false;
  bool wasConnected_ = false;
  bool justConnected_ = false;
};
