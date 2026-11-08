#include "net/WifiConnection.h"

#include <WiFi.h>

WifiConnection::WifiConnection(const char *ssid, const char *password, unsigned long retryMs)
    : ssid_(ssid), password_(password), retryMs_(retryMs) {}

void WifiConnection::begin() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
}

bool WifiConnection::ensure(unsigned long nowMs) {
  bool connected = WiFi.status() == WL_CONNECTED;
  justConnected_ = connected && !wasConnected_;

  if (justConnected_) {
    Serial.printf("[WiFi] Conectado, IP %s, RSSI %d dBm\n", WiFi.localIP().toString().c_str(),
                  WiFi.RSSI());
  } else if (!connected && wasConnected_) {
    Serial.println("[WiFi] Conexión perdida");
  }
  wasConnected_ = connected;

  if (connected) {
    return true;
  }

  if (!attempted_ || nowMs - lastAttemptMs_ >= retryMs_) {
    attempted_ = true;
    lastAttemptMs_ = nowMs;
    Serial.printf("[WiFi] Conectando a %s...\n", ssid_);
    WiFi.disconnect();
    WiFi.begin(ssid_, password_);
  }
  return false;
}
