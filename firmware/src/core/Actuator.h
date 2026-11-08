/**
 * @file    Actuator.h
 * @brief   Interfaz común para todos los actuadores del Vigilante Inteligente.
 *
 * Capa:        core (hardware)
 * Responsable: Ruben
 * Requisitos:  base de RF3 (servo como cerradura) y de futuros actuadores (buzzer).
 *
 * SmartObject (capa de Luciana) controla los actuadores a través de esta interfaz.
 * Cada actuador agrega sus propios métodos de acción (DoorLock: open()/close()),
 * pero todos se inicializan y se atienden en el loop de la misma forma.
 *
 * Regla: update() NO debe bloquear (sin delay()); se llama en cada vuelta de loop().
 */
#pragma once

class Actuator {
public:
    virtual ~Actuator() = default;

    /** Configura el hardware y lo lleva a un estado inicial conocido. Se llama en setup(). */
    virtual void begin() = 0;

    /** Tareas periódicas del actuador (p. ej. apagar un buzzer). Por defecto no hace nada. */
    virtual void update() {}

    /** Nombre corto para los mensajes del monitor serie. */
    virtual const char* name() const = 0;
};
