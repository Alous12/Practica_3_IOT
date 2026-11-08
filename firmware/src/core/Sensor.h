/**
 * @file    Sensor.h
 * @brief   Interfaz común para todos los sensores del Vigilante Inteligente.
 *
 * Capa:        core (hardware)
 * Responsable: Ruben
 * Requisitos:  base de RF1 (lectura del PIR) y de futuros sensores (LDR del láser KY-008).
 *
 * SmartObject (capa de Luciana) trabaja con sensores a través de esta interfaz.
 * Para agregar un sensor nuevo basta con heredar de Sensor e implementar sus métodos;
 * el resto del firmware no cambia (principio abierto/cerrado).
 *
 * Reglas para quien implemente un sensor:
 *  - update() NO debe bloquear (sin delay()): se llama en cada vuelta de loop().
 *  - consumeChange() devuelve true una sola vez por cada cambio de estado, para
 *    que SmartObject reporte al Shadow solo cuando hay un evento.
 */
#pragma once

class Sensor {
public:
    virtual ~Sensor() = default;

    /** Configura el pin y deja el sensor listo para leerse. Se llama una vez en setup(). */
    virtual void begin() = 0;

    /** Lee el hardware y actualiza el estado interno. Se llama en cada loop(). */
    virtual void update() = 0;

    /** true cuando las lecturas son confiables (p. ej. el PIR ya terminó de estabilizarse). */
    virtual bool isReady() const = 0;

    /** true una sola vez después de cada cambio de estado; la llamada lo "consume". */
    virtual bool consumeChange() = 0;

    /** Nombre corto para los mensajes del monitor serie. */
    virtual const char* name() const = 0;
};
