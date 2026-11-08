"""Frases en español que responde la skill."""
from typing import Optional


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
                  "pedirme que cierre o abra la puerta, o preguntar si la puerta está cerrada. "
                  "¿Qué deseas hacer?")
WELCOME_UNLINKED = ("Bienvenido a Vigilante Inteligente. Aún no tienes un dispositivo vinculado. "
                    "Di: vincula mi dispositivo con el código, seguido de los seis dígitos que "
                    "muestra tu dispositivo.")
NOT_LINKED = ("Aún no tienes un dispositivo vinculado. Di: vincula mi dispositivo con el código, "
              "seguido de los seis dígitos que muestra tu dispositivo.")
HELP = ("Puedes decir: vincula mi dispositivo con el código uno dos tres cuatro cinco seis; "
        "hay movimiento; cierra la puerta; abre la puerta; la puerta está cerrada; "
        "qué dispositivo tengo vinculado; o desvincula mi dispositivo. ¿Qué deseas hacer?")
REPROMPT = "¿Algo más?"
GOODBYE = "Hasta luego."
FALLBACK = "No entendí eso. Puedes decir ayuda para escuchar las opciones. ¿Qué deseas hacer?"
ERROR = "Lo siento, tuve un problema para hacer eso. Intenta de nuevo."
DEVICE_ERROR = "No pude comunicarme con AWS IoT. Intenta de nuevo en unos segundos."
NO_REPORT = "Tu dispositivo todavía no ha enviado datos. Verifica que esté encendido y conectado."
