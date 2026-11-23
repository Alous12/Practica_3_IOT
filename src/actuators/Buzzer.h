#pragma once

// BUZZER_ACTIVE decide los miembros de la clase: debe estar definido aquí, antes de la
// declaración, para que Buzzer tenga el mismo tamaño en todos los archivos (ODR).
#include "config.h"

#include <ESP32PWM.h>

#include "core/Actuator.h"

#ifndef BUZZER_ACTIVE
#error "BUZZER_ACTIVE debe definirse en include/config.h (1 = activo, 0 = pasivo)."
#endif

/**
 * Alarma con buzzer (segundo actuador).
 *
 * Capa: hardware (Alejandro). Requerimientos: RF3 aplicar órdenes del Shadow; RF2 exponer el estado.
 *
 * Atributo del Shadow: "alarma" = "encendida" | "apagada". Al encender el ESP32 queda apagada.
 * Mientras está encendida pita de forma intermitente (ALARM_BEEP_MS sí, ALARM_BEEP_MS no),
 * calculado con millis() en loop(), sin delay().
 *
 * BUZZER_ACTIVE (include/config.h):
 *   1 = buzzer activo: basta con poner el pin en alto (digitalWrite).
 *   0 = buzzer pasivo: necesita un tono PWM de BUZZER_TONE_HZ. Se usa ESP32PWM (de la
 *       biblioteca ESP32Servo), que reparte los canales LEDC junto con el servo: al pedir
 *       otra frecuencia (2 kHz contra 50 Hz) le asigna un canal y un timer distintos.
 *
 * Este actuador no decide cuándo sonar ni cuándo apagarse solo: eso lo hacen la regla
 * AlarmRule (Edge) y el Shadow (voz o Nube) con turnOn()/turnOff() y onSinceMs().
 */
class Buzzer : public Actuator {
 public:
  explicit Buzzer(uint8_t pin);

  const char *key() const override;
  void begin() override;
  void loop(unsigned long nowMs) override;
  bool applyDesired(JsonVariantConst value) override;
  void report(JsonObject reported) const override;

  /** Enciende la alarma; true si cambió (estaba apagada). */
  bool turnOn();
  /** Apaga la alarma; true si cambió (estaba encendida). */
  bool turnOff();
  bool isOn() const { return on_; }
  /** millis() del último encendido; solo tiene sentido si isOn(). */
  unsigned long onSinceMs() const { return onSinceMs_; }

 private:
  void writeSound(bool sounding);

  uint8_t pin_;
  bool on_ = false;          // estado lógico (lo que se reporta)
  bool sounding_ = false;    // fase del pitido intermitente (pin en alto o tono activo)
  unsigned long onSinceMs_ = 0;
#if BUZZER_ACTIVE == 0
  ESP32PWM pwm_;  // solo el buzzer pasivo necesita un canal LEDC
#endif
};
