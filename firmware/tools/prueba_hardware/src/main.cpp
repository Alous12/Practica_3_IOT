/**
 * @file    main.cpp (prueba_hardware)
 * @brief   Banco de pruebas del hardware: PIR + servo, sin WiFi ni AWS.
 *
 * Responsable: Ruben
 * Sirve para: RNF2 (exactitud del PIR), calibrar SERVO_ANGLE_CLOSED / SERVO_ANGLE_OPEN
 *             y revisar que no haya reinicios por brownout al mover el servo.
 *
 * Monitor serie a 115200 baudios. Comandos (una letra + Enter):
 *   c  cerrar la puerta          a  abrir la puerta
 *   +  servo +5°                 -  servo -5°        (para calibrar; muestra el ángulo)
 *   r  reiniciar el contador de detecciones (antes de cada distancia del RNF2)
 *   s  mostrar el estado
 */
#include <Arduino.h>
#include "config.h"
#include "sensors/PirSensor.h"
#include "actuators/DoorLock.h"

PirSensor pir(PIN_PIR);
DoorLock  lock(PIN_SERVO, SERVO_ANGLE_CLOSED, SERVO_ANGLE_OPEN);

int      calibAngle   = SERVO_ANGLE_CLOSED;
uint32_t countOffset  = 0;   // para reiniciar el conteo sin tocar PirSensor
uint32_t lastStatusMs = 0;

static void printStatus() {
    Serial.printf("[%6lu s] sensor_listo=%s movimiento=%s detecciones=%lu puerta=%s\n",
                  millis() / 1000UL,
                  pir.isReady() ? "true" : "false",
                  pir.isMotion() ? "true" : "false",
                  (unsigned long)(pir.detectionCount() - countOffset),
                  lock.isClosed() ? "cerrada" : "abierta");
}

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.printf("\nMotivo del último reinicio: %d (1=encendido, 15=brownout)\n",
                  (int)esp_reset_reason());
    pir.begin();
    lock.begin();
    Serial.println("Prueba de hardware lista. Esperando ~60 s de estabilización del PIR.");
    Serial.println("Comandos: c=cerrar a=abrir +/-=calibrar r=reiniciar conteo s=estado");
}

void loop() {
    pir.update();
    lock.update();

    if (pir.consumeChange()) printStatus();          // cada evento del PIR
    if (millis() - lastStatusMs >= 10000) {          // y un estado cada 10 s
        lastStatusMs = millis();
        printStatus();
    }

    if (!Serial.available()) return;
    switch (Serial.read()) {
        case 'c': lock.close(); calibAngle = SERVO_ANGLE_CLOSED; printStatus(); break;
        case 'a': lock.open();  calibAngle = SERVO_ANGLE_OPEN;   printStatus(); break;
        case '+': calibAngle = min(calibAngle + 5, 180); lock.moveTo(calibAngle);
                  Serial.printf("Ángulo de calibración: %d\n", calibAngle); break;
        case '-': calibAngle = max(calibAngle - 5, 0);   lock.moveTo(calibAngle);
                  Serial.printf("Ángulo de calibración: %d\n", calibAngle); break;
        case 'r': countOffset = pir.detectionCount();
                  Serial.println("Conteo reiniciado."); break;
        case 's': printStatus(); break;
        default: break;
    }
}
