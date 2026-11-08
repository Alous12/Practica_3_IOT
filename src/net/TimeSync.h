#pragma once

#include <stdint.h>

/**
 * Sincronización de hora por NTP (UTC).
 * Se usa solo para sellar la hora de la última detección y para medir
 * latencias en los logs; el sistema funciona aunque no haya hora.
 */
class TimeSync {
 public:
  /** Inicia la sincronización (llamar cuando haya WiFi). */
  static void begin();

  /** Hora actual en segundos epoch UTC, o 0 si aún no se sincronizó. */
  static uint32_t nowEpoch();

  /** Hora actual en milisegundos epoch UTC, o 0 si aún no se sincronizó. */
  static uint64_t nowEpochMs();
};
