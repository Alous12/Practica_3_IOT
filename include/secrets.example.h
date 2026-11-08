#pragma once

// ============================================================
//  PLANTILLA de credenciales (sin valores reales).
//  1. Copie este archivo como include/secrets.h
//  2. Complete los valores. secrets.h está en .gitignore y
//     NUNCA debe subirse al repositorio.
// ============================================================

#include <pgmspace.h>

// ---------- Red WiFi ----------
#define WIFI_SSID         "NOMBRE_DE_SU_RED"
#define WIFI_PASSWORD     "CLAVE_DE_SU_RED"

// ---------- AWS IoT Core ----------
// AWS IoT > Objetos > su Thing > Sombras de dispositivo > Sombra clásica:
// de la "URL de la sombra", la parte entre https:// y /things (termina en -ats.iot.us-east-2.amazonaws.com)
#define AWS_IOT_ENDPOINT  "xxxxxxxxxxxxxx-ats.iot.us-east-2.amazonaws.com"

// Debe ser EXACTAMENTE el nombre del Thing creado en AWS IoT.
// Formato: vigilante-<código de 6 dígitos que no empiece con 0>
#define THING_NAME        "vigilante-000000"

// Amazon Root CA 1 (archivo AmazonRootCA1.pem)
static const char AWS_ROOT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
PEGUE AQUÍ EL CONTENIDO DE AmazonRootCA1.pem
-----END CERTIFICATE-----
)EOF";

// Certificado del dispositivo (archivo ...-certificate.pem.crt)
static const char AWS_DEVICE_CERT[] PROGMEM = R"KEY(
-----BEGIN CERTIFICATE-----
PEGUE AQUÍ EL CERTIFICADO DEL THING
-----END CERTIFICATE-----
)KEY";

// Clave privada del dispositivo (archivo ...-private.pem.key)
static const char AWS_PRIVATE_KEY[] PROGMEM = R"KEY(
-----BEGIN RSA PRIVATE KEY-----
PEGUE AQUÍ LA CLAVE PRIVADA DEL THING
-----END RSA PRIVATE KEY-----
)KEY";
