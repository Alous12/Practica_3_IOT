#pragma once

// ============================================================
//  Configuración NO secreta del objeto inteligente.
//  Este archivo SÍ se sube al repositorio.
//  WiFi, endpoint, nombre del Thing y certificados van en
//  secrets.h (excluido por .gitignore; ver secrets.example.h).
// ============================================================

// Valores iniciales: los ángulos y tiempos requieren validación en el montaje.
// El PIR no acciona el servo localmente: el control procede del Shadow (RF3).

// ---------- Pines (ESP32 DOIT DevKit V1) ----------
#define PIR_PIN               27   // salida digital del HC-SR501 (3.3 V)
#define SERVO_PIN             25   // señal PWM del servo SG90 (se movió de GPIO 13 durante el diagnóstico)

// ---------- Sensor PIR (HC-SR501) ----------
// El HC-SR501 necesita ~60 s tras energizarse para estabilizarse.
#define PIR_WARMUP_MS         60000UL

// ---------- Actuador: cerradura con servo SG90 ----------
#define SERVO_ANGLE_CLOSED    90    // grados con la puerta cerrada (ajustar al montaje)
#define SERVO_ANGLE_OPEN      0     // grados con la puerta abierta
#define SERVO_SETTLE_MS       700UL // tiempo de movimiento antes de soltar el servo

// ---------- Device Shadow ----------
#define MQTT_PORT             8883
#define MQTT_BUFFER_SIZE      2048  // get/accepted trae desired+reported+delta+metadata (>256 B)
#define THING_PREFIX          "vigilante-"  // los Things se llaman vigilante-<código de 6 dígitos>

// Atributos del Shadow (deben coincidir con la Lambda)
#define KEY_DOOR              "puerta"            // "abierta" | "cerrada"  (desired y reported)
#define KEY_MOTION            "movimiento"        // bool                   (reported)
#define KEY_DETECTIONS        "detecciones"       // int, desde el encendido (reported)
#define KEY_LAST_DETECTION    "ultima_deteccion"  // epoch s UTC, 0 = sin hora (reported)
#define KEY_SENSOR_READY      "sensor_listo"      // bool, false durante el calentamiento
#define KEY_UPTIME            "uptime_s"          // int (reported, para la prueba de estabilidad)
#define KEY_RSSI              "rssi"              // dBm (reported)

#define DOOR_OPEN             "abierta"
#define DOOR_CLOSED           "cerrada"

// ---------- Frecuencia de reporte ----------
// Reporte por EVENTO: cada cambio del PIR o del actuador se publica de inmediato,
// respetando una separación mínima entre publicaciones (anti-ráfagas).
// Reporte PERIÓDICO de respaldo (heartbeat): estado completo cada 60 s.
#define REPORT_MIN_GAP_MS     500UL
#define REPORT_PERIOD_MS      60000UL

// ---------- Reconexión ----------
#define WIFI_RETRY_MS         5000UL
#define MQTT_RETRY_MS         5000UL

// ---------- Hora (NTP) para sellar la última detección ----------
#define NTP_SERVER_1          "pool.ntp.org"
#define NTP_SERVER_2          "time.google.com"

// ---------- Depuración ----------
#define SERIAL_BAUD           115200
