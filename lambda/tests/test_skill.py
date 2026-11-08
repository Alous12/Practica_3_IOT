"""Pruebas de los requerimientos RF4–RF9 de la skill con dobles de AWS.

Ejecutar desde la carpeta lambda/:
    pip install -r requirements-dev.txt
    python -m pytest -v
"""
import json

import pytest

from tests.harness import EVENTS, NOW, OTHER, THING, Harness


@pytest.fixture
def h():
    return Harness()


def linked(h):
    h.say("02_vincular.json")
    return h


# ---------- RF7, RF8, RF9: vinculación ----------

def test_launch_sin_vinculacion_guia_al_usuario(h):
    assert "Aún no tienes un dispositivo vinculado" in h.say("01_launch.json")


def test_comando_sin_vinculacion_indica_como_vincular(h):
    assert "Aún no tienes un dispositivo vinculado" in h.say("05_cerrar_puerta.json")


def test_vincular_thing_existente_persiste_en_dynamodb(h):
    text = h.say("02_vincular.json")
    assert "vinculé tu dispositivo 123456" in text
    item = h.db.items["amzn1.ask.account.USUARIO_DE_PRUEBA"]
    assert item["thingName"]["S"] == THING
    assert item["fechaVinculacion"]["S"].endswith("Z")


def test_vincular_thing_inexistente_se_rechaza(h):
    text = h.say("02_vincular.json", codigo="111111")
    assert "No encontré ningún dispositivo" in text
    assert h.db.items == {}


def test_codigo_con_formato_invalido_se_rechaza(h):
    assert "seis dígitos" in h.say("02_vincular.json", codigo="1234")


def test_cambiar_vinculacion(h):
    linked(h)
    text = h.say("02_vincular.json", codigo="654321")
    assert "cambié tu vinculación" in text
    assert h.db.items["amzn1.ask.account.USUARIO_DE_PRUEBA"]["thingName"]["S"] == OTHER


def test_consultar_vinculacion(h):
    linked(h)
    assert "123456" in h.say("03_consultar_vinculacion.json")


def test_desvincular_confirmado_elimina_registro(h):
    linked(h)
    assert "desvinculé" in h.say("08_desvincular.json")
    assert h.db.items == {}


def test_desvincular_denegado_conserva_registro(h):
    linked(h)
    assert "sigue vinculado" in h.say("08_desvincular.json", confirmation="DENIED")
    assert h.db.items


# ---------- RF4: consulta del sensor ----------

def test_movimiento_detectado(h):
    linked(h)
    h.data.set_reported(THING, movimiento=True, detecciones=3, ultima_deteccion=NOW,
                        sensor_listo=True, puerta="cerrada")
    text = h.say("04_consultar_movimiento.json")
    assert "Se está detectando movimiento" in text
    assert "Detecciones desde que se encendió: 3" in text


def test_sin_movimiento_indica_ultima_deteccion(h):
    linked(h)
    h.data.set_reported(THING, movimiento=False, detecciones=1, ultima_deteccion=NOW - 600,
                        sensor_listo=True, puerta="cerrada")
    text = h.say("04_consultar_movimiento.json")
    assert "No se detecta movimiento" in text
    assert "hace 10 minutos" in text


def test_sensor_en_calentamiento(h):
    linked(h)
    h.data.set_reported(THING, movimiento=False, detecciones=0, sensor_listo=False)
    assert "calibrando" in h.say("04_consultar_movimiento.json")


def test_dispositivo_sin_reportes(h):
    linked(h)
    assert "todavía no ha enviado datos" in h.say("04_consultar_movimiento.json")


def test_aviso_de_dispositivo_desconectado(h):
    linked(h)
    h.data.now = NOW - 1000
    h.data.set_reported(THING, movimiento=False, detecciones=0, sensor_listo=True)
    assert "puede estar desconectado" in h.say("04_consultar_movimiento.json")


# ---------- RF5 y RF6: actuador ----------

def test_cerrar_puerta_actualiza_desired_y_confirma(h):
    linked(h)
    h.data.set_reported(THING, puerta="abierta")
    text = h.say("05_cerrar_puerta.json")
    assert "la puerta quedó cerrada" in text
    assert h.data.shadows[THING]["state"]["desired"]["puerta"] == "cerrada"


def test_abrir_puerta(h):
    linked(h)
    h.data.set_reported(THING, puerta="cerrada")
    assert "la puerta quedó abierta" in h.say("06_abrir_puerta.json")


def test_puerta_ya_en_el_estado_pedido(h):
    linked(h)
    h.data.set_reported(THING, puerta="cerrada")
    assert "ya está cerrada" in h.say("05_cerrar_puerta.json")


def test_comando_con_dispositivo_desconectado_queda_pendiente():
    h = Harness(device_online=False)
    linked(h)
    h.data.set_reported(THING, puerta="abierta")
    text = h.say("05_cerrar_puerta.json")
    assert "aún no la confirmó" in text
    assert h.clock.t >= 3.0  # esperó el tiempo de confirmación configurado
    assert "orden pendiente" in h.say("07_estado_puerta.json")


def test_estado_de_la_puerta(h):
    linked(h)
    h.data.set_reported(THING, puerta="cerrada")
    assert "La puerta está cerrada" in h.say("07_estado_puerta.json")


def test_usuarios_distintos_controlan_things_distintos(h):
    """La skill no está atada a un único Thing."""
    linked(h)
    event = json.loads((EVENTS / "02_vincular.json").read_text(encoding="utf-8"))
    for section in (event["session"]["user"], event["context"]["System"]["user"]):
        section["userId"] = "amzn1.ask.account.OTRO_USUARIO"
    event["request"]["intent"]["slots"]["codigo"]["value"] = "654321"
    h.handler(event, None)
    assert h.db.items["amzn1.ask.account.USUARIO_DE_PRUEBA"]["thingName"]["S"] == THING
    assert h.db.items["amzn1.ask.account.OTRO_USUARIO"]["thingName"]["S"] == OTHER
