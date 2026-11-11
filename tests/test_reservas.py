"""Pruebas del módulo de reservas."""
from datetime import date, timedelta

import pytest

MANANA = (date.today() + timedelta(days=1)).isoformat()
AYER = (date.today() - timedelta(days=1)).isoformat()


def _reserva(c, mesa_id, hora="19:00", fecha=MANANA, personas=2):
    return c.post("/reservas", json={"mesa_id": mesa_id, "fecha": fecha,
                                     "hora": hora, "personas": personas})


def test_crear_reserva(cliente, mesa):
    r = _reserva(cliente, mesa["id"])
    assert r.status_code == 201
    datos = r.get_json()
    assert datos["estado"] == "activa" and datos["hora"] == "19:00" and datos["fecha"] == MANANA


def test_reserva_requiere_sesion(anonimo, mesa):
    assert _reserva(anonimo, mesa["id"]).status_code == 401


@pytest.mark.parametrize("cambio", [
    {"fecha": AYER},
    {"fecha": "2026-13-40"},
    {"fecha": "2026-1-5"},
    {"fecha": 20261105},
    {"hora": "10:59"},
    {"hora": "21:01"},
    {"hora": "25:00"},
    {"hora": "7pm"},
    {"personas": 0},
    {"personas": "dos"},
    {"personas": 5},          # la mesa de la prueba tiene capacidad 4
    {"mesa_id": 999},
    {"mesa_id": None},
])
def test_reserva_invalida(cliente, mesa, cambio):
    cuerpo = {"mesa_id": mesa["id"], "fecha": MANANA, "hora": "19:00", "personas": 2, **cambio}
    assert cliente.post("/reservas", json=cuerpo).status_code == 422


def test_limites_del_horario_se_aceptan(cliente, mesa):
    assert _reserva(cliente, mesa["id"], hora="11:00").status_code == 201
    assert _reserva(cliente, mesa["id"], hora="21:00").status_code == 201


def test_conflicto_de_horario_en_la_misma_mesa(cliente, mesero, mesa):
    assert _reserva(cliente, mesa["id"], hora="19:00").status_code == 201
    assert _reserva(mesero, mesa["id"], hora="20:30").status_code == 409   # se solapa
    assert _reserva(mesero, mesa["id"], hora="18:30").status_code == 409   # se solapa
    assert _reserva(mesero, mesa["id"], hora="21:00").status_code == 201   # justo 2 horas despues


def test_misma_hora_en_otra_mesa_o_fecha(admin, cliente, mesa):
    otra = admin.post("/mesas", json={"numero": 2, "capacidad": 6}).get_json()
    pasado_manana = (date.today() + timedelta(days=2)).isoformat()
    assert _reserva(cliente, mesa["id"]).status_code == 201
    assert _reserva(cliente, otra["id"]).status_code == 201
    assert _reserva(cliente, mesa["id"], fecha=pasado_manana).status_code == 201


def test_cancelar_libera_el_horario(cliente, mesero, mesa):
    rid = _reserva(cliente, mesa["id"]).get_json()["id"]
    r = cliente.delete(f"/reservas/{rid}")
    assert r.status_code == 200 and r.get_json()["estado"] == "cancelada"
    assert cliente.delete(f"/reservas/{rid}").status_code == 409
    assert _reserva(mesero, mesa["id"]).status_code == 201


def test_cliente_no_cancela_reservas_ajenas(app, cliente, mesero, mesa):
    rid = _reserva(mesero, mesa["id"]).get_json()["id"]
    assert cliente.delete(f"/reservas/{rid}").status_code == 404
    assert mesero.delete(f"/reservas/{rid}").status_code == 200


def test_listado_por_rol_y_fecha(cliente, mesero, mesa):
    propia = _reserva(cliente, mesa["id"], hora="12:00").get_json()["id"]
    _reserva(mesero, mesa["id"], hora="19:00")
    assert [r["id"] for r in cliente.get("/reservas").get_json()] == [propia]
    assert len(mesero.get("/reservas").get_json()) == 2
    assert len(mesero.get(f"/reservas?fecha={MANANA}").get_json()) == 2
    assert mesero.get("/reservas?fecha=2020-01-01").get_json() == []
    assert mesero.get("/reservas?fecha=hoy").status_code == 422
