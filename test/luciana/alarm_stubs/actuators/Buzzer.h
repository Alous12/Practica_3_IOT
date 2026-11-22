#pragma once

#include "Arduino.h"
#include "config.h"
#include "core/Actuator.h"

/** Doble de la API acordada. No controla GPIO/PWM y nunca se carga al ESP32. */
class Buzzer : public Actuator {
 public:
  int onCalls = 0, offCalls = 0;
  const char *key() const override { return KEY_ALARM; }
  void begin() override { on_ = false; since_ = 0; onCalls = offCalls = 0; }
  void loop(unsigned long) override {}
  bool applyDesired(JsonVariantConst value) override {
    const char *text = value.is<const char*>() ? value.as<const char*>() : nullptr;
    if (!text) return false;
    if (strcmp(text, ALARM_ON) == 0) turnOn();
    else if (strcmp(text, ALARM_OFF) == 0) turnOff();
    else return false;
    return true;
  }
  void report(JsonObject reported) const override {
    reported[KEY_ALARM] = on_ ? ALARM_ON : ALARM_OFF;
  }
  void turnOn() {
    ++onCalls;
    if (!on_) { on_ = true; since_ = millis(); }
  }
  void turnOff() { ++offCalls; on_ = false; }
  bool isOn() const { return on_; }
  unsigned long onSinceMs() const { return since_; }

 private:
  bool on_ = false;
  unsigned long since_ = 0;
};
