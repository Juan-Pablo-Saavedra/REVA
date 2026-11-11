"""Pruebas del cierre de caja y los reportes de ventas diarios."""
from datetime import date, timedelta

HOY = date.today().isoformat()
MANANA = (date.today() + timedelta(days=1)).isoformat()


def _vender(cliente, mesero, carta, cant_bandeja=1, cant_sopa=0, hasta="pagado"):
    items = [{"plato_id": carta["bandeja"]["id"], "cantidad": cant_bandeja}]
    if cant_sopa:
        items.append({"plato_id": carta["sopa"]["id"], "cantidad": cant_sopa})
    pid = cliente.post("/pedidos", json={"items": items}).get_json()["id"]
    camino = ["en_preparacion", "listo", "entregado", "pagado"]
    for estado in camino[: camino.index(hasta) + 1]:
        assert mesero.patch(f"/pedidos/{pid}/estado", json={"estado": estado}).status_code == 200
    return pid


def test_reporte_solo_para_administrador(anonimo, cliente, mesero):
    assert anonimo.get("/caja/reporte").status_code == 401
    assert cliente.get("/caja/reporte").status_code == 403
    assert mesero.get("/caja/reporte").status_code == 403


def test_reporte_de_un_dia_sin_ventas(admin):
    r = admin.get("/caja/reporte")
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["total_ventas"] == 0 and datos["num_pedidos"] == 0
    assert datos["ticket_promedio"] == 0 and datos["platos_mas_vendidos"] == []


def test_reporte_suma_solo_pedidos_pagados(admin, cliente, mesero, carta):
    _vender(cliente, mesero, carta, cant_bandeja=2, cant_sopa=1)            # 89.000
    _vender(cliente, mesero, carta, cant_bandeja=1)                         # 32.000
    _vender(cliente, mesero, carta, cant_bandeja=5, hasta="listo")          # no cuenta
    pid = cliente.post("/pedidos", json={"items": [
        {"plato_id": carta["sopa"]["id"], "cantidad": 3}]}).get_json()["id"]
    mesero.patch(f"/pedidos/{pid}/estado", json={"estado": "cancelado"})    # no cuenta
    datos = admin.get(f"/caja/reporte?fecha={HOY}").get_json()
    assert datos["num_pedidos"] == 2
    assert datos["total_ventas"] == 89000 + 32000
    assert datos["ticket_promedio"] == round((89000 + 32000) / 2)


def test_platos_mas_vendidos(admin, cliente, mesero, carta):
    _vender(cliente, mesero, carta, cant_bandeja=3, cant_sopa=1)
    top = admin.get("/caja/reporte").get_json()["platos_mas_vendidos"]
    assert top[0] == {"nombre": "Bandeja paisa", "unidades": 3, "ingresos": 96000}
    assert top[1]["nombre"] == "Sancocho"


def test_reporte_valida_la_fecha(admin):
    for fecha in ("hoy", "2026-13-01", MANANA, "2026-1-1"):
        assert admin.get(f"/caja/reporte?fecha={fecha}").status_code == 422


def test_cierre_de_caja(admin, cliente, mesero, carta):
    _vender(cliente, mesero, carta, cant_bandeja=2)
    r = admin.post("/caja/cierre", json={"fecha": HOY})
    assert r.status_code == 201
    assert r.get_json() == {"fecha": HOY, "total_ventas": 64000, "num_pedidos": 1}
    registro = admin.get("/caja/cierres").get_json()
    assert registro[0]["fecha"] == HOY and registro[0]["total_ventas"] == 64000


def test_no_se_cierra_dos_veces_el_mismo_dia(admin):
    assert admin.post("/caja/cierre", json={"fecha": HOY}).status_code == 201
    assert admin.post("/caja/cierre", json={"fecha": HOY}).status_code == 409


def test_no_se_cierra_con_pedidos_por_cobrar(admin, cliente, mesero, carta):
    _vender(cliente, mesero, carta, hasta="entregado")
    r = admin.post("/caja/cierre", json={"fecha": HOY})
    assert r.status_code == 409 and r.get_json()["pedidos_por_cobrar"] == 1


def test_cierre_valida_fecha_y_rol(admin, mesero):
    assert admin.post("/caja/cierre", json={"fecha": MANANA}).status_code == 422
    assert admin.post("/caja/cierre", json={}).status_code == 422
    assert admin.post("/caja/cierre", data="x").status_code == 400
    assert mesero.post("/caja/cierre", json={"fecha": HOY}).status_code == 403
