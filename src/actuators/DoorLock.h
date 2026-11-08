#pragma once

#include <ESP32Servo.h>

#include "core/Actuator.h"

/**
 * Cerradura de la puerta accionada por un servo SG90.
 *
 * Capa: hardware (Ruben). Requerimientos: RF3 aplicar órdenes del Shadow; RF2 exponer el estado.
 *
 * El brazo del servo es el pestillo: SERVO_ANGLE_CLOSED lo interpone delante de la hoja
 * de la puerta y SERVO_ANGLE_OPEN la libera (ángulos en include/config.h).
 *
 * El SG90 no mide posición: reported expresa la posición ordenada, no una
 * confirmación física del pestillo. Calibrar y verificar el movimiento en la demo.
 * Atributo del Shadow: "puerta" = "abierta" | "cerrada".
 * El servo se energiza solo mientras se mueve (SERVO_SETTLE_MS) y luego se
 * suelta, para evitar vibraciones y reducir el consumo.
 */
class DoorLock : public Actuator {
 public:
  DoorLock(uint8_t pin, int closedAngle, int openAngle, unsigned long settleMs);

  const char *key() const override;
  void begin() override;
  void loop(unsigned long nowMs) override;
  bool applyDesired(JsonVariantConst value) override;
  void report(JsonObject reported) const override;

  bool isClosed() const { return closed_; }

  /**
   * Solo para calibrar (tools/prueba_hardware): mueve el servo a un ángulo libre
   * (0–180) sin cambiar el estado reportado. Se suelta igual tras settleMs.
   */
  void calibrate(int angle);

 private:
  void moveTo(bool closed);

  Servo servo_;
  uint8_t pin_;
  int closedAngle_;
  int openAngle_;
  unsigned long settleMs_;
  bool closed_ = true;  // estado seguro por defecto: cerrada
  bool moving_ = false;
  unsigned long moveStartedMs_ = 0;
};
