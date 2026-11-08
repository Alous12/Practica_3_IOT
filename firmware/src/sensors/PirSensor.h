/**
 * @file    PirSensor.h
 * @brief   Sensor de presencia PIR HC-SR501 (RF1: lectura del PIR).
 *
 * Capa:        sensors (hardware)
 * Responsable: Ruben
 *
 * Qué hace:
 *  - Lee la salida digital del HC-SR501 (OUT = 3,3 V, directo al GPIO, sin divisor).
 *  - Filtra pulsos espurios (debounce) para que el ruido del servo no cuente como movimiento.
 *  - Durante el calentamiento (~60 s) informa isReady() = false y NO cuenta detecciones,
 *    porque el HC-SR501 da falsos positivos mientras se estabiliza (sensor_listo en el Shadow).
 *  - Cuenta las detecciones (flancos de subida) y guarda cuándo fue la última.
 *
 * Ajustes físicos del módulo: jumper en H (disparo repetible), Tx al mínimo (~3 s),
 * Sx al medio. Con H, OUT queda en alto mientras haya movimiento y baja ~3 s después.
 *
 * Uso esperado desde SmartObject (Luciana):
 *   PirSensor pir(PIN_PIR);
 *   pir.begin();                              // en setup()
 *   pir.update();                             // en cada loop()
 *   if (pir.consumeChange()) { ...reportar movimiento/detecciones al Shadow... }
 *   reported.movimiento   = pir.isMotion();
 *   reported.detecciones  = pir.detectionCount();
 *   reported.sensor_listo = pir.isReady();
 *   // ultima_deteccion (epoch): SmartObject lo toma de TimeSync cuando
 *   // consumeChange() es true y isMotion() es true, o lo calcula con lastDetectionMs().
 */
#pragma once

#include <Arduino.h>
#include "core/Sensor.h"

class PirSensor : public Sensor {
public:
    /**
     * @param pin        GPIO conectado a OUT del HC-SR501.
     * @param warmupMs   Tiempo de estabilización tras el encendido (hoja de datos: 30–60 s).
     * @param debounceMs Tiempo que la señal debe mantenerse estable para aceptarse.
     */
    explicit PirSensor(uint8_t pin, uint32_t warmupMs = 60000, uint32_t debounceMs = 50);

    // --- Sensor ---
    void begin() override;
    void update() override;
    bool isReady() const override;
    bool consumeChange() override;
    const char* name() const override { return "PIR"; }

    // --- Propios del PIR ---
    /** true mientras se detecta movimiento (siempre false durante el calentamiento). */
    bool isMotion() const { return motion_; }

    /** Detecciones (flancos de subida) desde el encendido; no cuenta el calentamiento. */
    uint32_t detectionCount() const { return detections_; }

    /** millis() de la última detección, o 0 si todavía no hubo ninguna. */
    uint32_t lastDetectionMs() const { return lastDetectionMs_; }

private:
    const uint8_t  pin_;
    const uint32_t warmupMs_;
    const uint32_t debounceMs_;

    uint32_t startMs_         = 0;     // millis() en begin(), para medir el calentamiento
    bool     ready_           = false; // terminó el calentamiento
    bool     rawLevel_        = false; // última lectura cruda del pin
    uint32_t rawSinceMs_      = 0;     // desde cuándo la lectura cruda no cambia
    bool     motion_          = false; // estado filtrado (lo que se reporta)
    uint32_t detections_      = 0;
    uint32_t lastDetectionMs_ = 0;
    bool     changed_         = false; // hay un cambio pendiente de reportar
};
