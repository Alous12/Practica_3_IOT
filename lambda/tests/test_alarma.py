"""Pruebas de la alarma (buzzer): EncenderAlarmaIntent, ApagarAlarmaIntent y EstadoAlarmaIntent.

Atributo del Shadow alarma = "encendida" | "apagada". La skill lo escribe en desired con
"origen": "voz" y espera a que el ESP32 lo confirme en reported, igual que con la puerta.
"""
import pytest

from tests.harness import THING, Harness
from vigilante.device_state import DeviceState


@pytest.fixture
def h():
    harness = Harness()
    harness.say("02_vincular.json")
    harness.data.set_reported(THING, puerta="cerrada", modo="manual", alarma="apagada",
                              origen="inicio", sensor_listo=True)
    return harness


def desired(h):
    return h.shadow_state()["desired"]


def reported(h):
    return h.shadow_state()["reported"]


# ---------- EncenderAlarmaIntent / ApagarAlarmaIntent ----------

def test_encender_alarma_escribe_desired_con_origen_voz_y_confirma(h):
    text = h.say("15_encender_alarma.json")
    assert "Listo, la alarma quedó encendida" in text
    assert desired(h) == {"alarma": "encendida", "origen": "voz"}
    assert reported(h)["alarma"] == "encendida"


def test_apagar_alarma(h):
    h.data.set_reported(THING, alarma="encendida", origen="edge")
    text = h.say("16_apagar_alarma.json")
    assert "Listo, la alarma quedó apagada" in text
    assert desired(h) == {"alarma": "apagada", "origen": "voz"}
    assert reported(h)["origen"] == "voz"


def test_encender_alarma_ya_encendida_no_escribe(h):
    h.data.set_reported(THING, alarma="encendida")
    assert "La alarma ya está encendida" in h.say("15_encender_alarma.json")
    assert "desired" not in h.shadow_state()


def test_apagar_alarma_ya_apagada_no_escribe(h):
    assert "La alarma ya está apagada" in h.say("16_apagar_alarma.json")
    assert "desired" not in h.shadow_state()


def test_alarma_sin_confirmar_queda_pendiente():
    h = Harness(device_online=False)
    h.say("02_vincular.json")
    h.data.set_reported(THING, alarma="apagada")
    assert "aún no la confirmó" in h.say("15_encender_alarma.json")
    assert h.clock.t >= 3.0                         # esperó el tiempo de confirmación
    assert "orden pendiente para dejarla encendida" in h.say("17_estado_alarma.json")


def test_alarma_sin_vinculacion_indica_como_vincular():
    h = Harness()
    assert "Aún no tienes un dispositivo vinculado" in h.say("15_encender_alarma.json")
    assert h.data.shadows == {}


# ---------- EstadoAlarmaIntent ----------

def test_estado_alarma_apagada(h):
    text = h.say("17_estado_alarma.json")
    assert text.startswith("La alarma está apagada.")


def test_estado_alarma_encendida_por_voz_no_dice_quien(h):
    h.data.set_reported(THING, alarma="encendida", origen="voz")
    text = h.say("17_estado_alarma.json")
    assert "La alarma está sonando." in text
    assert "La activó" not in text


def test_estado_alarma_activada_por_el_edge(h):
    h.data.set_reported(THING, alarma="encendida", origen="edge")
    assert "La activó el sistema automáticamente al detectar movimiento" in h.say(
        "17_estado_alarma.json")


def test_estado_alarma_activada_por_la_nube(h):
    h.data.set_reported(THING, alarma="encendida", origen="nube")
    assert "La activó la nube" in h.say("17_estado_alarma.json")


def test_estado_alarma_con_firmware_sin_alarma():
    h = Harness()
    h.say("02_vincular.json")
    h.data.set_reported(THING, puerta="cerrada")
    assert "todavía no informó el estado de la alarma" in h.say("17_estado_alarma.json")


def test_estado_alarma_sin_reportes():
    h = Harness()
    h.say("02_vincular.json")
    assert "todavía no ha enviado datos" in h.say("17_estado_alarma.json")


# ---------- Cambio a modo manual apaga la alarma ----------

def test_pasar_a_manual_apaga_la_alarma_en_el_mismo_desired(h):
    h.data.set_reported(THING, modo="bloqueo", alarma="encendida", origen="nube")
    text = h.set_mode("manual")
    assert "cambié al modo manual" in text
    assert "También envié la orden de apagar la alarma" in text
    assert desired(h) == {"modo": "manual", "alarma": "apagada", "origen": "voz"}
    assert reported(h)["alarma"] == "apagada"


def test_pasar_a_manual_con_alarma_apagada_no_la_menciona(h):
    h.data.set_reported(THING, modo="automatico")
    text = h.set_mode("manual")
    assert "alarma" not in text
    assert desired(h)["alarma"] == "apagada"


@pytest.mark.parametrize("mode", ["automatico", "bloqueo"])
def test_pasar_a_automatico_o_bloqueo_no_toca_la_alarma(h, mode):
    h.set_mode(mode)
    assert "alarma" not in desired(h)


# ---------- DeviceState ----------

def test_device_state_lee_la_alarma():
    state = DeviceState.from_shadow({"state": {
        "desired": {"alarma": "apagada", "origen": "voz"},
        "reported": {"alarma": "encendida", "origen": "nube"}}})
    assert state.alarm == "encendida"
    assert state.desired_alarm == "apagada"
    assert state.alarm_pending
    assert state.origin == "nube"


def test_device_state_alarma_en_null_no_es_pendiente():
    state = DeviceState.from_shadow({"state": {
        "desired": {"alarma": None}, "reported": {"alarma": "encendida"}}})
    assert not state.alarm_pending


def test_la_ayuda_menciona_la_alarma():
    assert "enciende la alarma" in Harness().ask("AMAZON.HelpIntent")
