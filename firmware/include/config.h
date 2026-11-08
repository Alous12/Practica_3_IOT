/**
 * @file    config.h
 * @brief   Configuración del firmware del Vigilante Inteligente.
 *
 * Archivo compartido. Cada integrante edita SOLO su sección y hace git pull antes.
 *  - Hardware (Ruben):       pines y ángulos del servo.
 *  - Comunicación (Luciana): claves del Shadow, valores de la puerta, prefijo del Thing,
 *                            tiempos de reporte y latido.
 */
#pragma once

// =====================================================================================
// HARDWARE — Ruben
// Conexiones (ESP32 DOIT DevKit V1):
//   PIR HC-SR501: VCC -> VIN (5 V) | OUT -> GPIO 27 (3,3 V, sin divisor) | GND -> GND
//   Servo SG90:   rojo -> VIN (5 V) | naranja -> GPIO 13              | marrón -> GND
//   Condensador 470 µF / 16 V entre VIN (+) y GND (-), lo más cerca del servo.
// =====================================================================================

#define PIN_PIR   27   // salida digital del PIR (entrada del ESP32)
#define PIN_SERVO 13   // señal PWM del servo

// Ángulos del pestillo (grados, 0–180). Calibrar sobre la maqueta.
#define SERVO_ANGLE_CLOSED 90   // pestillo trabando la puerta
#define SERVO_ANGLE_OPEN   0    // pestillo liberado

// =====================================================================================
// COMUNICACIÓN — Luciana
// (claves del Shadow, valores de la puerta, prefijo del Thing y tiempos)
// =====================================================================================
