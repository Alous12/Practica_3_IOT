/**
 * @file    PirSensor.cpp
 * @brief   Implementación del sensor PIR HC-SR501 (RF1).
 *
 * Responsable: Ruben
 *
 * Todas las comparaciones de tiempo usan restas de millis() (ahora - inicio), que siguen
 * funcionando cuando millis() se desborda a los ~49 días.
 */
#include "sensors/PirSensor.h"

PirSensor::PirSensor(uint8_t pin, uint32_t warmupMs, uint32_t debounceMs)
    : pin_(pin), warmupMs_(warmupMs), debounceMs_(debounceMs) {}

void PirSensor::begin() {
    // El HC-SR501 maneja OUT activamente (alto/bajo). El pull-down solo evita lecturas
    // flotantes (falsos positivos) si el cable de OUT se suelta.
    pinMode(pin_, INPUT_PULLDOWN);
    startMs_    = millis();
    ready_      = (warmupMs_ == 0);
    rawLevel_   = digitalRead(pin_) == HIGH;
    rawSinceMs_ = startMs_;
    motion_     = false;
    changed_    = true;  // primer reporte: movimiento=false, sensor_listo=false
}

void PirSensor::update() {
    const uint32_t now = millis();

    // 1) Fin del calentamiento: se avisa una vez para que el Shadow pase sensor_listo a true.
    if (!ready_ && now - startMs_ >= warmupMs_) {
        ready_   = true;
        changed_ = true;
    }

    // 2) Debounce: se acepta un nivel solo si se mantuvo estable debounceMs_.
    const bool level = digitalRead(pin_) == HIGH;
    if (level != rawLevel_) {
        rawLevel_   = level;
        rawSinceMs_ = now;
        return;
    }
    if (now - rawSinceMs_ < debounceMs_) return;

    // 3) Mientras calienta, el estado se fuerza a "sin movimiento" y no se cuenta nada.
    const bool newMotion = ready_ && level;
    if (newMotion == motion_) return;

    motion_  = newMotion;
    changed_ = true;
    if (motion_) {  // flanco de subida = una detección nueva
        detections_++;
        lastDetectionMs_ = now == 0 ? 1 : now;  // 0 está reservado para "ninguna"
    }
}

bool PirSensor::isReady() const {
    return ready_;
}

bool PirSensor::consumeChange() {
    const bool c = changed_;
    changed_ = false;
    return c;
}
