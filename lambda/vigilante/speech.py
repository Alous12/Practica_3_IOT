"""Frases en español que responde la skill."""
from typing import Optional

from .config import (
    ALARM_ON,
    MAX_DETECTIONS_MAX,
    MAX_DETECTIONS_MIN,
    MODE_AUTO,
    MODE_LOCKDOWN,
    MODE_MANUAL,
    ORIGIN_BOOT,
    ORIGIN_CLOUD,
    ORIGIN_EDGE,
    WINDOW_MINUTES_MAX,
    WINDOW_MINUTES_MIN,
)

# En el Shadow los modos van sin tilde; Alexa los dice con la ortografía correcta.
MODE_NAMES = {MODE_MANUAL: "manual", MODE_AUTO: "automático", MODE_LOCKDOWN: "bloqueo"}
MODE_DESCRIPTIONS = {
    MODE_MANUAL: "la puerta solo se abre o se cierra cuando tú lo pides",
    MODE_AUTO: "la puerta se cierra sola cuando el sensor detecta movimiento",
    MODE_LOCKDOWN: ("la puerta se cierra sola cuando el sensor detecta movimiento y "
                "queda bloqueada para abrirla por voz"),
}


def mode_name(mode: Optional[str]) -> str:
    return MODE_NAMES.get(mode, mode or "desconocido")


def minutes(value: int) -> str:
    return "{} {}".format(value, "minuto" if value == 1 else "minutos")


def mode_changed(mode: str) -> str:
    return "Listo, cambié al modo {}: {}.".format(mode_name(mode), MODE_DESCRIPTIONS[mode])


def mode_already(mode: str) -> str:
    return "El dispositivo ya está en modo {}.".format(mode_name(mode))


def mode_pending(mode: str) -> str:
    return ("Envié el cambio al modo {}, pero el dispositivo aún no lo confirmó. "
            "Se aplicará en cuanto se conecte.".format(mode_name(mode)))


def mode_status(mode: str) -> str:
    return "El dispositivo está en modo {}: {}.".format(mode_name(mode), MODE_DESCRIPTIONS[mode])


def mode_pending_note(mode: str) -> str:
    return " Hay un cambio pendiente al modo {}.".format(mode_name(mode))


def open_rejected(mode: str) -> str:
    """Respuesta a "abre la puerta" en modo automático o bloqueo."""
    return ("No puedo abrir la puerta porque el dispositivo está en modo {}: {}. "
            "Si quieres abrirla, primero di: cambia el modo a manual."
            .format(mode_name(mode), MODE_DESCRIPTIONS[mode]))


def max_detections_changed(value: int) -> str:
    return "Listo, el máximo de detecciones ahora es {}.".format(value)


def max_detections_already(value: int) -> str:
    return "El máximo de detecciones ya es {}.".format(value)


def max_detections_pending(value: int) -> str:
    return ("Envié el cambio del máximo de detecciones a {}, pero el dispositivo aún no lo "
            "confirmó. Se aplicará en cuanto se conecte.".format(value))


def window_changed(value: int) -> str:
    return "Listo, la ventana de detecciones ahora es de {}.".format(minutes(value))


def window_already(value: int) -> str:
    return "La ventana de detecciones ya es de {}.".format(minutes(value))


def window_pending(value: int) -> str:
    return ("Envié el cambio de la ventana a {}, pero el dispositivo aún no lo confirmó. "
            "Se aplicará en cuanto se conecte.".format(minutes(value)))


def alarm_changed(alarm: str) -> str:
    return "Listo, la alarma quedó {}.".format(alarm)


def alarm_already(alarm: str) -> str:
    return "La alarma ya está {}.".format(alarm)


def alarm_pending(verb: str) -> str:
    return ("Envié la orden de {} la alarma, pero el dispositivo aún no la confirmó. "
            "Se aplicará en cuanto se conecte.".format(verb))


def alarm_status(alarm: str, origin: Optional[str]) -> str:
    """Estado de la alarma y, si suena por una regla, quién la activó."""
    if alarm != ALARM_ON:
        return "La alarma está apagada."
    text = "La alarma está sonando."
    if origin == ORIGIN_EDGE:
        text += " La activó el sistema automáticamente al detectar movimiento."
    elif origin == ORIGIN_CLOUD:
        text += (" La activó la nube al superar el máximo de detecciones "
                 "dentro de la ventana configurada.")
    return text


def alarm_pending_note(alarm: str) -> str:
    return " Hay una orden pendiente para dejarla {}.".format(alarm)


MANUAL_ALARM_OFF = " También envié la orden de apagar la alarma."


def door_origin(door: Optional[str], origin: Optional[str]) -> str:
    """Explica quién dejó la puerta así, si no fue una orden de voz."""
    if origin == ORIGIN_EDGE and door == "cerrada":
        return " La cerró el sistema automáticamente al detectar movimiento."
    if origin == ORIGIN_BOOT:
        return " Quedó así al encenderse el dispositivo."
    return ""


def digits(code: str) -> str:
    """SSML para que Alexa lea un código dígito por dígito."""
    return '<say-as interpret-as="digits">{}</say-as>'.format(code)


def elapsed(seconds: int) -> str:
    """Convierte segundos a una expresión natural: 'hace 3 minutos'."""
    if seconds < 60:
        return "hace menos de un minuto"
    minutes = seconds // 60
    if minutes < 60:
        return "hace {} {}".format(minutes, "minuto" if minutes == 1 else "minutos")
    hours = minutes // 60
    if hours < 24:
        return "hace {} {}".format(hours, "hora" if hours == 1 else "horas")
    days = hours // 24
    return "hace {} {}".format(days, "día" if days == 1 else "días")


def stale_warning(seconds_since_report: Optional[int], stale_after_s: int) -> str:
    """Aviso si el dispositivo no reporta desde hace demasiado (posible desconexión)."""
    if seconds_since_report is None or seconds_since_report <= stale_after_s:
        return ""
    return (" Ojo: el dispositivo no se comunica desde {}, puede estar desconectado."
            .format(elapsed(seconds_since_report)))


WELCOME_LINKED = ("Bienvenido a Vigilante Inteligente. Puedes preguntarme si hay movimiento, "
                  "pedirme que cierre o abra la puerta, encender o apagar la alarma, "
                  "o cambiar el modo de operación. ¿Qué deseas hacer?")
WELCOME_UNLINKED = ("Bienvenido a Vigilante Inteligente. Aún no tienes un dispositivo vinculado. "
                    "Di: vincula mi dispositivo con el código, seguido de los seis dígitos que "
                    "muestra tu dispositivo.")
NOT_LINKED = ("Aún no tienes un dispositivo vinculado. Di: vincula mi dispositivo con el código, "
              "seguido de los seis dígitos que muestra tu dispositivo.")
HELP = ("Puedes decir: vincula mi dispositivo con el código uno dos tres cuatro cinco seis; "
        "hay movimiento; cierra la puerta; abre la puerta; la puerta está cerrada; "
        "enciende la alarma; apaga la alarma; está sonando la alarma; "
        "cambia el modo a manual, automático o bloqueo; en qué modo está; "
        "cambia el máximo de detecciones a cinco; cambia la ventana a diez minutos; "
        "cuáles son los parámetros; qué dispositivo tengo vinculado; "
        "o desvincula mi dispositivo. ¿Qué deseas hacer?")
ASK_MODE = "¿Qué modo quieres? Puedes decir manual, automático o bloqueo."
ASK_MAX_DETECTIONS = ("¿Cuál debe ser el máximo de detecciones? Di un número entre {} y {}."
                      .format(MAX_DETECTIONS_MIN, MAX_DETECTIONS_MAX))
ASK_WINDOW = ("¿De cuántos minutos debe ser la ventana? Di un número entre {} y {}."
              .format(WINDOW_MINUTES_MIN, WINDOW_MINUTES_MAX))
MAX_DETECTIONS_OUT_OF_RANGE = ("El máximo de detecciones debe ser un número entre {} y {}."
                               .format(MAX_DETECTIONS_MIN, MAX_DETECTIONS_MAX))
WINDOW_OUT_OF_RANGE = ("La ventana debe ser un número de minutos entre {} y {}."
                       .format(WINDOW_MINUTES_MIN, WINDOW_MINUTES_MAX))
NO_ALARM = ("Tu dispositivo todavía no informó el estado de la alarma. "
            "Verifica que esté encendido y con el firmware actualizado.")
NO_MODE = ("Tu dispositivo todavía no informó su modo de operación. "
           "Verifica que esté encendido y con el firmware actualizado.")
REPROMPT = "¿Algo más?"
GOODBYE = "Hasta luego."
FALLBACK = "No entendí eso. Puedes decir ayuda para escuchar las opciones. ¿Qué deseas hacer?"
ERROR = "Lo siento, tuve un problema para hacer eso. Intenta de nuevo."
DEVICE_ERROR = "No pude comunicarme con AWS IoT. Intenta de nuevo en unos segundos."
NO_REPORT = "Tu dispositivo todavía no ha enviado datos. Verifica que esté encendido y conectado."
