"""Pruebas de la ampliación: modo de operación, parámetros y origen de los cambios.

Intents nuevos: CambiarModoIntent, ConsultarModoIntent, CambiarMaxDeteccionesIntent,
CambiarVentanaIntent y ConsultarParametrosIntent. Todo desired que escribe la skill lleva
"origen": "voz"; "abre la puerta" se rechaza en modo automático o bloqueo.
"""
import pytest

from tests.harness import THING, Harness
from vigilante.device_state import DeviceState


@pytest.fixture
def h():
    harness = Harness()
    harness.say("02_vincular.json")
    harness.data.set_reported(THING, puerta="abierta", modo="manual", max_detecciones=5,
                              ventana_min=10, origen="inicio", sensor_listo=True)
    return harness


def desired(h):
    return h.shadow_state()["desired"]


def reported(h):
    return h.shadow_state()["reported"]


# ---------- CambiarModoIntent ----------

def test_cambiar_modo_escribe_desired_con_origen_voz_y_confirma(h):
    text = h.say("10_cambiar_modo.json")
    assert "cambié al modo automático" in text
    assert "se cierra sola" in text
    assert desired(h) == {"modo": "automatico", "origen": "voz"}
    assert reported(h)["modo"] == "automatico"
    assert reported(h)["origen"] == "voz"


@pytest.mark.parametrize("spoken, canonical", [
    ("automático", "automatico"), ("auto", "automatico"),
    ("bloqueado", "bloqueo"), ("normal", "manual"),
])
def test_cambiar_modo_usa_el_valor_canonico_de_alexa(h, spoken, canonical):
    h.data.set_reported(THING, modo="manual" if canonical != "manual" else "bloqueo")
    h.set_mode(canonical, spoken=spoken)
    assert desired(h)["modo"] == canonical


def test_cambiar_modo_sin_resoluciones_quita_tildes(h):
    """Un evento de la consola de Lambda sin `resolutions` también funciona."""
    h.ask("CambiarModoIntent", slots={"modo": "Automático"})
    assert desired(h)["modo"] == "automatico"


def test_modo_no_reconocido_pide_el_modo_y_no_escribe(h):
    text = h.ask("CambiarModoIntent", slots={"modo": "turbo"}, resolved={"modo": None})
    assert "Puedes decir manual, automático o bloqueo" in text
    assert "desired" not in h.shadow_state()


def test_cambiar_modo_sin_slot_pide_el_modo(h):
    assert "¿Qué modo quieres?" in h.ask("CambiarModoIntent")


def test_modo_ya_aplicado_no_escribe(h):
    assert "ya está en modo manual" in h.set_mode("manual")
    assert "desired" not in h.shadow_state()


def test_manual_ya_aplicado_con_la_alarma_apagada_no_escribe(h):
    h.data.set_reported(THING, alarma="apagada")
    text = h.set_mode("manual")
    assert text.startswith("El dispositivo ya está en modo manual.")
    assert "alarma" not in text
    assert "desired" not in h.shadow_state()


def test_manual_ya_aplicado_con_la_alarma_sonando_la_apaga(h):
    """"activa el modo manual" estando ya en manual también silencia la alarma."""
    h.data.set_reported(THING, alarma="encendida", origen="edge")
    text = h.set_mode("manual")
    assert "ya está en modo manual" in text
    assert "Apagué la alarma" in text
    assert desired(h) == {"alarma": "apagada", "origen": "voz"}
    assert reported(h)["alarma"] == "apagada"
    assert reported(h)["modo"] == "manual"


def test_manual_ya_aplicado_con_la_alarma_sin_confirmar_queda_pendiente():
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, modo="manual", alarma="encendida")
    text = h.set_mode("manual")
    assert "ya está en modo manual" in text
    assert "aún no la confirmó" in text
    assert h.shadow_state()["desired"] == {"alarma": "apagada", "origen": "voz"}


def test_pasar_a_bloqueo_cierra_la_puerta_en_el_mismo_desired(h):
    """Igual que vigilante-logica: bloqueo lleva "puerta": "cerrada" junto al modo."""
    text = h.set_mode("bloqueo")                       # el fixture deja la puerta abierta
    assert "cambié al modo bloqueo" in text
    assert "También envié la orden de cerrar la puerta" in text
    assert desired(h) == {"modo": "bloqueo", "puerta": "cerrada", "origen": "voz"}
    assert reported(h)["puerta"] == "cerrada"


def test_pasar_a_bloqueo_con_la_puerta_cerrada_no_lo_menciona(h):
    h.data.set_reported(THING, puerta="cerrada")
    text = h.set_mode("bloqueo")
    assert "cerrar la puerta" not in text
    assert desired(h)["puerta"] == "cerrada"


def test_pasar_a_automatico_no_toca_la_puerta(h):
    h.set_mode("automatico")
    assert "puerta" not in desired(h)


def test_bloqueo_sin_confirmar_deja_pendiente_tambien_la_puerta():
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, modo="manual", puerta="abierta")
    assert "aún no lo confirmó" in h.set_mode("bloqueo")
    assert "orden pendiente para dejarla cerrada" in h.say("07_estado_puerta.json")


def test_cambio_de_modo_sin_confirmar_queda_pendiente():
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, modo="manual", puerta="cerrada")
    assert "aún no lo confirmó" in h.set_mode("bloqueo")
    assert h.clock.t >= 3.0
    assert "cambio pendiente al modo bloqueo" in h.say("11_consultar_modo.json")


def test_modo_bloqueo_por_voz_tambien_cierra_la_puerta(h):
    """"activa el modo bloqueo": igual que el bloqueo de la Nube, deja la puerta cerrada."""
    text = h.set_mode("bloqueo")
    assert desired(h) == {"modo": "bloqueo", "puerta": "cerrada", "origen": "voz"}
    assert "aún no lo confirmó" not in text  # se esperó y se confirmó el modo
    assert reported(h)["modo"] == "bloqueo"
    assert reported(h)["puerta"] == "cerrada"
    assert reported(h)["origen"] == "voz"


# ---------- ConsultarModoIntent ----------

@pytest.mark.parametrize("mode, spoken", [
    ("manual", "modo manual"), ("automatico", "modo automático"), ("bloqueo", "modo bloqueo"),
])
def test_consultar_modo(h, mode, spoken):
    h.data.set_reported(THING, modo=mode)
    assert spoken in h.say("11_consultar_modo.json")


def test_consultar_modo_con_firmware_sin_modo():
    h = Harness()
    h.say("02_vincular.json")
    h.data.set_reported(THING, puerta="cerrada")
    assert "todavía no informó su modo" in h.say("11_consultar_modo.json")


# ---------- "abre la puerta" según el modo ----------

@pytest.mark.parametrize("mode, spoken", [("automatico", "automático"), ("bloqueo", "bloqueo")])
def test_abrir_se_rechaza_en_automatico_y_bloqueo(h, mode, spoken):
    h.data.set_reported(THING, modo=mode, puerta="cerrada")
    text = h.say("06_abrir_puerta.json")
    assert "No puedo abrir la puerta" in text
    assert "modo " + spoken in text
    assert "cambia el modo a manual" in text
    assert "desired" not in h.shadow_state()          # no se envió ninguna orden


def test_abrir_se_permite_en_manual(h):
    h.data.set_reported(THING, puerta="cerrada")
    assert "la puerta quedó abierta" in h.say("06_abrir_puerta.json")
    assert desired(h) == {"puerta": "abierta", "origen": "voz"}


def test_abrir_se_rechaza_si_hay_un_cambio_pendiente_a_automatico():
    """Si el ESP32 aún no aplicó "modo automático", manda lo último que pidió el usuario."""
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, modo="manual", puerta="cerrada")
    h.set_mode("automatico")
    assert "No puedo abrir la puerta" in h.say("06_abrir_puerta.json")


def test_cerrar_se_permite_en_bloqueo(h):
    h.data.set_reported(THING, modo="bloqueo", puerta="abierta")
    assert "la puerta quedó cerrada" in h.say("05_cerrar_puerta.json")


# ---------- CambiarMaxDeteccionesIntent ----------

@pytest.mark.parametrize("value", ["1", "7", "20"])
def test_cambiar_max_detecciones_en_rango(h, value):
    text = h.say("12_cambiar_max_detecciones.json", numero=value)
    assert "el máximo de detecciones ahora es " + value in text
    assert desired(h) == {"max_detecciones": int(value), "origen": "voz"}


@pytest.mark.parametrize("value", ["0", "21", "100", "?"])
def test_max_detecciones_fuera_de_rango_no_escribe(h, value):
    assert "entre 1 y 20" in h.say("12_cambiar_max_detecciones.json", numero=value)
    assert "desired" not in h.shadow_state()


def test_max_detecciones_sin_numero_lo_pide(h):
    assert "¿Cuál debe ser el máximo" in h.ask("CambiarMaxDeteccionesIntent")


def test_max_detecciones_igual_al_actual(h):
    assert "ya es 5" in h.say("12_cambiar_max_detecciones.json", numero="5")
    assert "desired" not in h.shadow_state()


# ---------- CambiarVentanaIntent ----------

@pytest.mark.parametrize("value, spoken", [("1", "1 minuto"), ("30", "30 minutos"),
                                           ("120", "120 minutos")])
def test_cambiar_ventana_en_rango(h, value, spoken):
    text = h.say("13_cambiar_ventana.json", minutos=value)
    assert "la ventana de detecciones ahora es de " + spoken in text
    assert desired(h) == {"ventana_min": int(value), "origen": "voz"}


@pytest.mark.parametrize("value", ["0", "121", "?"])
def test_ventana_fuera_de_rango_no_escribe(h, value):
    assert "entre 1 y 120" in h.say("13_cambiar_ventana.json", minutos=value)
    assert "desired" not in h.shadow_state()


def test_ventana_sin_numero_la_pide(h):
    assert "¿De cuántos minutos" in h.ask("CambiarVentanaIntent")


# ---------- ConsultarParametrosIntent ----------

def test_consultar_parametros(h):
    text = h.say("14_consultar_parametros.json")
    assert "Modo manual" in text
    assert "Máximo de detecciones: 5" in text
    assert "Ventana: 10 minutos" in text


def test_consultar_parametros_con_cambio_pendiente():
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, modo="manual", max_detecciones=5, ventana_min=10)
    h.say("13_cambiar_ventana.json", minutos="30")
    text = h.say("14_consultar_parametros.json")
    assert "Ventana: 10 minutos" in text          # lo que confirmó el dispositivo
    assert "cambios pendientes" in text


def test_consultar_parametros_sin_reportes():
    h = Harness()
    h.say("02_vincular.json")
    assert "todavía no ha enviado datos" in h.say("14_consultar_parametros.json")


# ---------- Origen de los cambios ----------

def test_estado_de_la_puerta_cerrada_por_el_edge(h):
    """La regla del Edge cierra la puerta y borra desired (puerta y origen en null)."""
    h.say("06_abrir_puerta.json")                        # desired.puerta = abierta (voz)
    h.data.set_reported(THING, modo="automatico", puerta="cerrada", origen="edge")
    h.data.clear_desired(THING, "puerta", "origen")       # la regla del Edge borra desired
    assert h.shadow_state()["desired"] == {}
    text = h.say("07_estado_puerta.json")
    assert "La puerta está cerrada" in text
    assert "La cerró el sistema automáticamente" in text
    assert "pendiente" not in text


def test_estado_de_la_puerta_al_encender(h):
    h.data.set_reported(THING, puerta="cerrada", origen="inicio")
    assert "al encenderse el dispositivo" in h.say("07_estado_puerta.json")


def test_estado_de_la_puerta_por_voz_no_agrega_origen(h):
    h.data.set_reported(THING, puerta="cerrada", origen="voz")
    assert h.say("07_estado_puerta.json").startswith("La puerta está cerrada.")


def test_desired_en_null_no_es_una_orden_pendiente():
    state = DeviceState.from_shadow({"state": {
        "desired": {"puerta": None, "origen": None},
        "reported": {"puerta": "cerrada", "origen": "edge", "modo": "automatico"}}})
    assert not state.door_pending
    assert state.origin == "edge"
    assert state.target_mode == "automatico"


def test_device_state_lee_modo_y_parametros():
    state = DeviceState.from_shadow({"state": {
        "desired": {"modo": "bloqueo", "origen": "voz"},
        "reported": {"modo": "manual", "max_detecciones": 3, "ventana_min": 15}}})
    assert (state.mode, state.max_detections, state.window_min) == ("manual", 3, 15)
    assert state.mode_pending and state.target_mode == "bloqueo"
    assert state.is_pending("origen")            # aún no lo copió a reported
