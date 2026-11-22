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
#define BUZZER_PIN            26   // señal del buzzer (alarma); suelto: a través de 220 Ω

// ---------- Sensor PIR (HC-SR501) ----------
// El HC-SR501 necesita ~60 s tras energizarse para estabilizarse.
#define PIR_WARMUP_MS         60000UL

// ---------- Actuador: cerradura con servo SG90 ----------
#define SERVO_ANGLE_CLOSED    90    // grados con la puerta cerrada (ajustar al montaje)
#define SERVO_ANGLE_OPEN      0     // grados con la puerta abierta
#define SERVO_SETTLE_MS       700UL // tiempo de movimiento antes de soltar el servo

// ---------- Actuador: alarma con buzzer ----------
#define BUZZER_ACTIVE         1         // 1 = buzzer activo (pita con nivel alto); 0 = pasivo (necesita PWM)
#define BUZZER_TONE_HZ        2000      // frecuencia del tono si el buzzer es pasivo
#define ALARM_BEEP_MS         500UL     // pitido intermitente: 500 ms sí, 500 ms no
#define ALARM_MAX_MS          30000UL   // la alarma se apaga sola tras 30 s (AlarmRule)

// ---------- Device Shadow ----------
#define MQTT_PORT             8883
#define MQTT_BUFFER_SIZE      3072  // get/accepted trae desired+reported+delta+metadata (>256 B)
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

#define KEY_ALARM             "alarma"            // "encendida" | "apagada"  (desired y reported)
#define ALARM_ON              "encendida"
#define ALARM_OFF             "apagada"

// ---------- Modo de operación, parámetros y origen (deben coincidir con la Lambda) ----------
#define KEY_MODE              "modo"              // desired y reported
#define KEY_MAX_DETECTIONS    "max_detecciones"   // int (desired y reported)
#define KEY_WINDOW_MIN        "ventana_min"       // int, minutos (desired y reported)
#define KEY_ORIGIN            "origen"            // quién causó el último cambio

#define MODE_MANUAL           "manual"            // la puerta solo obedece a la voz
#define MODE_AUTO             "automatico"        // la regla del Edge cierra la puerta al detectar movimiento
#define MODE_LOCKDOWN         "bloqueo"           // ídem; la puerta no se abre por voz

#define ORIGIN_VOICE          "voz"               // orden de Alexa (la Lambda de la skill)
#define ORIGIN_EDGE           "edge"              // la regla local del ESP32
#define ORIGIN_CLOUD          "nube"              // una regla en la nube
#define ORIGIN_BOOT           "inicio"            // valor al encender

#define DEFAULT_MAX_DETECTIONS 3
#define MAX_DETECTIONS_MIN    1
#define MAX_DETECTIONS_MAX    20

#define DEFAULT_WINDOW_MIN    10                  // minutos
#define WINDOW_MINUTES_MIN    1
#define WINDOW_MINUTES_MAX    120

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
