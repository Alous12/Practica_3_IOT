"""Guion completo del simulador de Alexa (Guía, Parte E4) ejecutado contra la skill real.

Cada paso corresponde a una frase que se escribe en la pestaña *Test* de la Alexa Developer
Console. Si estas pruebas pasan, el mismo guion en el simulador solo puede fallar por la
configuración de AWS/Alexa (endpoint, permisos, Skill ID), no por la lógica de la skill.

Escenario: el dueño tiene el ESP32 real (vigilante-123456) y un Thing de prueba sin hardware
(vigilante-654321). Un segundo usuario de Alexa vincula su propio Thing.
"""
from tests.harness import NOW, OTHER, OTHER_CODE, THING, THING_CODE, Harness

SEGUNDO_USUARIO = "amzn1.ask.account.SEGUNDO_USUARIO"


def _esp32_reporta(h, **reported):
    """Simula un shadow/update del ESP32 (lo que se ve en la Sombra clásica)."""
    base = dict(puerta="abierta", movimiento=False, detecciones=0, ultima_deteccion=0,
                sensor_listo=True, uptime_s=120, rssi=-58)
    base.update(reported)
    h.data.set_reported(THING, **base)


def test_guion_del_simulador_usuario_principal():
    h = Harness(offline_things={OTHER})          # el Thing de prueba no tiene hardware

    # 1. "abre vigilante inteligente" -> sin vinculación, guía para vincular (RF8)
    assert "Aún no tienes un dispositivo vinculado" in h.launch()

    # 2. "cierra la puerta" sin vinculación -> no toca ningún Shadow (RF8)
    assert "vincula mi dispositivo con el código" in h.ask("CerrarPuertaIntent")
    assert h.data.shadows == {}

    # 3. "vincula mi dispositivo con el código 111111" -> sí -> rechazo (RF9, validación)
    assert "No encontré ningún dispositivo con el código 111111" in h.ask(
        "VincularDispositivoIntent", codigo="111111")
    assert h.linked_thing() is None

    # 4. "vincula mi dispositivo con el código 654321" -> sí -> acepta (RF7)
    assert "vinculé tu dispositivo " + OTHER_CODE in h.ask(
        "VincularDispositivoIntent", codigo=OTHER_CODE)
    assert h.linked_thing() == OTHER

    # 5. "cierra la puerta" sobre el Thing sin hardware -> orden queda pendiente
    assert "aún no la confirmó" in h.ask("CerrarPuertaIntent")
    assert h.shadow_state(OTHER)["desired"] == {"puerta": "cerrada"}

    # 6. "cambia mi dispositivo al código 123456" -> sí -> cambio de vinculación (RF9)
    text = h.ask("VincularDispositivoIntent", codigo=THING_CODE)
    assert "cambié tu vinculación del dispositivo {} al dispositivo {}".format(
        OTHER_CODE, THING_CODE) in text
    assert h.linked_thing() == THING
    assert len(h.db.items) == 1                    # se reemplaza, no se duplica

    # 7. "qué dispositivo tengo vinculado" (RF8)
    assert "Tienes vinculado el dispositivo " + THING_CODE in h.ask("ConsultarVinculacionIntent")

    # 8. "hay movimiento" sin presencia (RF4)
    _esp32_reporta(h)
    assert "No se detecta movimiento" in h.ask("ConsultarMovimientoIntent")

    # 9. Pasan la mano frente al PIR -> "hay movimiento" (RF1, RF2, RF4)
    _esp32_reporta(h, movimiento=True, detecciones=1, ultima_deteccion=NOW)
    text = h.ask("ConsultarMovimientoIntent")
    assert "Se está detectando movimiento" in text
    assert "Detecciones desde que se encendió: 1" in text

    # 10. "cierra la puerta" -> desired, el ESP32 confirma en reported (RF5, RF3)
    inicio = h.clock.t
    assert "Listo, la puerta quedó cerrada" in h.ask("CerrarPuertaIntent")
    state = h.shadow_state(THING)
    assert state["desired"]["puerta"] == state["reported"]["puerta"] == "cerrada"
    assert h.clock.t - inicio < h.settings.confirm_timeout_s   # confirmó antes del límite

    # 11. "la puerta está cerrada" (RF6)
    assert "La puerta está cerrada" in h.ask("EstadoPuertaIntent")

    # 12. "abre la puerta" (RF5)
    assert "Listo, la puerta quedó abierta" in h.ask("AbrirPuertaIntent")
    assert "La puerta está abierta" in h.ask("EstadoPuertaIntent")

    # 13. "desvincula mi dispositivo" -> no -> se conserva (RF9)
    assert "sigue vinculado" in h.ask("DesvincularDispositivoIntent", confirmation="DENIED")
    assert h.linked_thing() == THING

    # 14. "desvincula mi dispositivo" -> sí -> se elimina (RF9)
    assert "desvinculé tu dispositivo" in h.ask("DesvincularDispositivoIntent",
                                                confirmation="CONFIRMED")
    assert h.linked_thing() is None
    assert "Aún no tienes un dispositivo vinculado" in h.ask("EstadoPuertaIntent")

    # 15. "salir"
    assert h.ask("AMAZON.StopIntent") == "Hasta luego."
    assert h.session_ended


def test_guion_segundo_usuario_controla_solo_su_thing():
    """Dos cuentas de Alexa, cada una con su Thing (la skill no está atada a un Thing fijo)."""
    h = Harness(offline_things={OTHER})
    _esp32_reporta(h, puerta="abierta")
    h.ask("VincularDispositivoIntent", codigo=THING_CODE)

    # El segundo usuario abre la skill: no hereda la vinculación del primero (RF8)
    assert "Aún no tienes un dispositivo vinculado" in h.launch(user_id=SEGUNDO_USUARIO)
    assert "vinculé tu dispositivo " + OTHER_CODE in h.ask(
        "VincularDispositivoIntent", user_id=SEGUNDO_USUARIO, codigo=OTHER_CODE)

    # Dos filas en DynamoDB, una por userId
    assert h.linked_thing() == THING
    assert h.linked_thing(SEGUNDO_USUARIO) == OTHER

    # El comando del segundo usuario va a SU Shadow y no mueve la puerta del primero
    h.ask("CerrarPuertaIntent", user_id=SEGUNDO_USUARIO)
    assert h.shadow_state(OTHER)["desired"]["puerta"] == "cerrada"
    assert "desired" not in h.shadow_state(THING)
    assert "La puerta está abierta" in h.ask("EstadoPuertaIntent")

    # Desvincular a uno no afecta al otro
    h.ask("DesvincularDispositivoIntent", user_id=SEGUNDO_USUARIO, confirmation="CONFIRMED")
    assert h.linked_thing(SEGUNDO_USUARIO) is None
    assert h.linked_thing() == THING


def test_guion_reconexion_aplica_la_orden_pendiente():
    """RNF5 visto desde Alexa: orden dada con el ESP32 desconectado se aplica al reconectar."""
    h = Harness(offline_things={THING})
    _esp32_reporta(h, puerta="cerrada")
    h.ask("VincularDispositivoIntent", codigo=THING_CODE)

    # Durante el corte de red: "abre la puerta"
    assert "aún no la confirmó" in h.ask("AbrirPuertaIntent")
    assert "Hay una orden pendiente para dejarla abierta" in h.ask("EstadoPuertaIntent")

    # Vuelve la red: el ESP32 pide shadow/get, aplica el delta y confirma en reported
    h.data.reconnect(THING)
    text = h.ask("EstadoPuertaIntent")
    assert "La puerta está abierta" in text
    assert "pendiente" not in text


def test_guion_ayuda_y_frases_no_reconocidas():
    h = Harness()
    assert "vincula mi dispositivo con el código" in h.ask("AMAZON.HelpIntent")
    assert "No entendí" in h.ask("AMAZON.FallbackIntent")
    assert not h.session_ended
    assert h.ask("AMAZON.CancelIntent") == "Hasta luego."
    assert h.session_ended
