/**
 * @file    DoorLock.h
 * @brief   Cerradura de la puerta con un servo SG90 (RF3: servo como cerradura).
 *
 * Capa:        actuators (hardware)
 * Responsable: Ruben
 *
 * Qué hace:
 *  - Mueve el brazo del servo (pestillo) a dos posiciones: cerrada y abierta.
 *  - Recuerda el estado actual para que SmartObject lo confirme en reported.puerta.
 *  - No usa delay(): el movimiento lo hace el servo solo (~0,15 s por 60° en el SG90),
 *    así que la confirmación al Shadow sale de inmediato y la Lambda la ve antes de 3 s.
 *
 * Los ángulos salen de config.h (SERVO_ANGLE_CLOSED / SERVO_ANGLE_OPEN) y se calibran
 * sobre la maqueta.
 *
 * Uso esperado desde SmartObject (Luciana), al recibir un delta del Shadow:
 *   DoorLock lock(PIN_SERVO, SERVO_ANGLE_CLOSED, SERVO_ANGLE_OPEN);
 *   lock.begin();                             // en setup(): arranca cerrada
 *   lock.setClosed(strcmp(deseado, DOOR_CLOSED) == 0);
 *   reported.puerta = lock.isClosed() ? DOOR_CLOSED : DOOR_OPEN;
 */
#pragma once

#include <Arduino.h>
#include <ESP32Servo.h>
#include "core/Actuator.h"

class DoorLock : public Actuator {
public:
    /**
     * @param pin          GPIO de la señal del servo (cable naranja/amarillo).
     * @param angleClosed  Ángulo con el pestillo trabando la puerta.
     * @param angleOpen    Ángulo con el pestillo liberado.
     * @param startClosed  Estado al encender. Cerrada por seguridad: si el Shadow pide
     *                     "abierta", el delta llega al conectarse y se corrige.
     */
    DoorLock(uint8_t pin, int angleClosed, int angleOpen, bool startClosed = true);

    // --- Actuator ---
    void begin() override;
    const char* name() const override { return "Cerradura"; }

    // --- Propios de la cerradura ---
    void close() { setClosed(true); }
    void open()  { setClosed(false); }

    /**
     * Lleva la puerta al estado pedido.
     * @return true si el servo se movió; false si ya estaba en ese estado.
     *         Aunque devuelva false, SmartObject igual debe confirmar en reported.
     */
    bool setClosed(bool closed);

    bool isClosed() const { return closed_; }

    /** Solo para calibrar: mueve el servo a un ángulo libre (0–180). No cambia isClosed(). */
    void moveTo(int angle);

private:
    Servo         servo_;
    const uint8_t pin_;
    const int     angleClosed_;
    const int     angleOpen_;
    bool          closed_;
};
