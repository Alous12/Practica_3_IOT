/**
 * @file    DoorLock.cpp
 * @brief   Implementación de la cerradura con servo SG90 (RF3).
 *
 * Responsable: Ruben
 */
#include "actuators/DoorLock.h"

namespace {
// Pulso del SG90: 50 Hz, ~500 µs = 0° y ~2400 µs = 180°.
// Si el servo no llega a los extremos o zumba contra el tope, ajustar aquí.
constexpr int SERVO_FREQ_HZ = 50;
constexpr int SERVO_MIN_US  = 500;
constexpr int SERVO_MAX_US  = 2400;
}  // namespace

DoorLock::DoorLock(uint8_t pin, int angleClosed, int angleOpen, bool startClosed)
    : pin_(pin), angleClosed_(angleClosed), angleOpen_(angleOpen), closed_(startClosed) {}

void DoorLock::begin() {
    servo_.setPeriodHertz(SERVO_FREQ_HZ);
    servo_.attach(pin_, SERVO_MIN_US, SERVO_MAX_US);
    // Estado inicial conocido: se mueve siempre, aunque el servo ya estuviera ahí.
    servo_.write(closed_ ? angleClosed_ : angleOpen_);
}

bool DoorLock::setClosed(bool closed) {
    if (closed == closed_) return false;  // ya está así: no se mueve (evita picos de corriente)
    closed_ = closed;
    servo_.write(closed_ ? angleClosed_ : angleOpen_);
    return true;
}

void DoorLock::moveTo(int angle) {
    servo_.write(constrain(angle, 0, 180));
}
