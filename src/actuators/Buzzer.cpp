/**
 * Implementación de la alarma con buzzer (RF3).
 * Capa: hardware (Alejandro).
 *
 * El pitido intermitente se calcula en loop() a partir de millis(): no hay delay(),
 * así que el PIR, el servo y MQTT siguen atendiéndose mientras suena.
 */
#include "actuators/Buzzer.h"

#include <Arduino.h>

#include "config.h"

namespace {
constexpr uint8_t PWM_RESOLUTION_BITS = 10;
constexpr double PWM_DUTY_ON = 0.5;  // onda cuadrada: máximo volumen en un buzzer pasivo
}  // namespace

Buzzer::Buzzer(uint8_t pin) : pin_(pin) {}

const char *Buzzer::key() const { return KEY_ALARM; }

void Buzzer::begin() {
#if BUZZER_ACTIVE
  pinMode(pin_, OUTPUT);
  digitalWrite(pin_, LOW);
#else
  pwm_.attachPin(pin_, BUZZER_TONE_HZ, PWM_RESOLUTION_BITS);
  pwm_.writeScaled(0.0);
#endif
  on_ = false;  // al encender el ESP32 la alarma queda apagada
  sounding_ = false;
}

void Buzzer::loop(unsigned long nowMs) {
  if (!on_) return;
  // Fase par = suena, fase impar = silencio (ALARM_BEEP_MS cada una).
  const bool shouldSound = ((nowMs - onSinceMs_) / ALARM_BEEP_MS) % 2 == 0;
  if (shouldSound != sounding_) writeSound(shouldSound);
}

bool Buzzer::applyDesired(JsonVariantConst value) {
  const char *text = value.is<const char *>() ? value.as<const char *>() : nullptr;
  if (text == nullptr) {
    Serial.println("[Alarma] Valor deseado inválido (se espera texto)");
    return false;
  }
  if (strcmp(text, ALARM_ON) == 0) {
    turnOn();
  } else if (strcmp(text, ALARM_OFF) == 0) {
    turnOff();
  } else {
    Serial.printf("[Alarma] Valor deseado desconocido: %s\n", text);
    return false;
  }
  return true;
}

void Buzzer::report(JsonObject reported) const {
  reported[KEY_ALARM] = on_ ? ALARM_ON : ALARM_OFF;
}

bool Buzzer::turnOn() {
  if (on_) return false;  // ya sonaba: no reiniciar el conteo de ALARM_MAX_MS
  on_ = true;
  onSinceMs_ = millis();
  writeSound(true);  // primer pitido inmediato
  Serial.println("[Alarma] Encendida");
  return true;
}

bool Buzzer::turnOff() {
  if (!on_) return false;
  on_ = false;
  writeSound(false);
  Serial.println("[Alarma] Apagada");
  return true;
}

void Buzzer::writeSound(bool sounding) {
  sounding_ = sounding;
#if BUZZER_ACTIVE
  digitalWrite(pin_, sounding ? HIGH : LOW);
#else
  pwm_.writeScaled(sounding ? PWM_DUTY_ON : 0.0);
#endif
}
