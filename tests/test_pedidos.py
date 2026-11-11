"""Pruebas del módulo de pedidos y de la gestión de mesas."""
import pytest


def _pedido(cliente, carta, mesa_id=None, cant_bandeja=2, cant_sopa=1):
    cuerpo = {"items": [
        {"plato_id": carta["bandeja"]["id"], "cantidad": cant_bandeja},
        {"plato_id": carta["sopa"]["id"], "cantidad": cant_sopa},
    ]}
    if mesa_id:
        cuerpo["mesa_id"] = mesa_id
    return cliente.post("/pedidos", json=cuerpo)


def test_crear_mesa_solo_administrador(admin, mesero):
    assert mesero.post("/mesas", json={"numero": 5, "capacidad": 2}).status_code == 403
    assert admin.post("/mesas", json={"numero": 5, "capacidad": 2}).status_code == 201
    assert admin.post("/mesas", json={"numero": 5, "capacidad": 6}).status_code == 409


def test_mesa_invalida(admin):
    assert admin.post("/mesas", json={"numero": 0, "capacidad": 4}).status_code == 422
    assert admin.post("/mesas", json={"numero": 2, "capacidad": "4"}).status_code == 422


def test_crear_pedido_calcula_el_total(cliente, carta, mesa):
    r = _pedido(cliente, carta, mesa["id"])
    assert r.status_code == 201
    pedido = r.get_json()
    assert pedido["estado"] == "pendiente"
    assert pedido["total"] == 2 * 32000 + 25000
    assert len(pedido["items"]) == 2


def test_pedido_requiere_sesion(anonimo, carta):
    assert _pedido(anonimo, carta).status_code == 401


@pytest.mark.parametrize("cuerpo", [
    {},
    {"items": []},
    {"items": "x"},
    {"items": [1]},
    {"items": [{"plato_id": 1, "cantidad": 0}]},
    {"items": [{"plato_id": 1, "cantidad": 21}]},
    {"items": [{"plato_id": 1, "cantidad": "2"}]},
    {"items": [{"plato_id": 9999, "cantidad": 1}]},
])
def test_pedido_invalido(cliente, carta, cuerpo):
    assert cliente.post("/pedidos", json=cuerpo).status_code == 422


def test_pedido_con_mesa_inexistente(cliente, carta):
    assert _pedido(cliente, carta, mesa_id=999).status_code == 422


def test_plato_no_disponible_no_se_puede_pedir(admin, cliente, carta):
    admin.put(f"/menu/platos/{carta['sopa']['id']}", json={"disponible": False})
    assert _pedido(cliente, carta).status_code == 422


def test_precio_del_pedido_no_cambia_si_cambia_el_menu(admin, cliente, carta):
    pedido = _pedido(cliente, carta, cant_bandeja=1, cant_sopa=1).get_json()
    admin.put(f"/menu/platos/{carta['bandeja']['id']}", json={"precio": 99000})
    consultado = cliente.get(f"/pedidos/{pedido['id']}").get_json()
    assert consultado["total"] == 32000 + 25000


def test_cliente_solo_ve_sus_pedidos(app, cliente, mesero, carta):
    propio = _pedido(cliente, carta).get_json()
    ajeno = _pedido(mesero, carta).get_json()
    assert cliente.get(f"/pedidos/{propio['id']}").status_code == 200
    assert cliente.get(f"/pedidos/{ajeno['id']}").status_code == 404
    assert [p["id"] for p in cliente.get("/pedidos").get_json()] == [propio["id"]]
    assert len(mesero.get("/pedidos").get_json()) == 2


def test_flujo_completo_de_estados(cliente, mesero, carta):
    pid = _pedido(cliente, carta).get_json()["id"]
    for estado in ("en_preparacion", "listo", "entregado", "pagado"):
        r = mesero.patch(f"/pedidos/{pid}/estado", json={"estado": estado})
        assert r.status_code == 200 and r.get_json()["estado"] == estado
    assert cliente.get(f"/pedidos/{pid}").get_json()["estado"] == "pagado"


def test_transicion_invalida(cliente, mesero, carta):
    pid = _pedido(cliente, carta).get_json()["id"]
    r = mesero.patch(f"/pedidos/{pid}/estado", json={"estado": "pagado"})
    assert r.status_code == 409


def test_estados_terminales_no_cambian(cliente, mesero, carta):
    pid = _pedido(cliente, carta).get_json()["id"]
    assert mesero.patch(f"/pedidos/{pid}/estado", json={"estado": "cancelado"}).status_code == 200
    assert mesero.patch(f"/pedidos/{pid}/estado", json={"estado": "en_preparacion"}).status_code == 409


def test_cliente_no_cambia_estados(cliente, carta):
    pid = _pedido(cliente, carta).get_json()["id"]
    r = cliente.patch(f"/pedidos/{pid}/estado", json={"estado": "en_preparacion"})
    assert r.status_code == 403


def test_estado_desconocido_y_pedido_inexistente(mesero, carta):
    assert mesero.patch("/pedidos/999/estado", json={"estado": "listo"}).status_code == 404
    assert mesero.patch("/pedidos/999/estado", json={"estado": "volando"}).status_code == 422


def test_filtrar_por_estado(cliente, mesero, carta):
    a = _pedido(cliente, carta).get_json()["id"]
    _pedido(cliente, carta)
    mesero.patch(f"/pedidos/{a}/estado", json={"estado": "en_preparacion"})
    r = mesero.get("/pedidos?estado=en_preparacion")
    assert [p["id"] for p in r.get_json()] == [a]
    assert mesero.get("/pedidos?estado=raro").status_code == 422


def test_plato_con_pedidos_no_se_elimina_pero_se_oculta(admin, cliente, carta):
    _pedido(cliente, carta)
    pid = carta["bandeja"]["id"]
    assert admin.delete(f"/menu/platos/{pid}").status_code == 409
    assert admin.get(f"/menu/platos/{pid}").get_json()["disponible"] is False
