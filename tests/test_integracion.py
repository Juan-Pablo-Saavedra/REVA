"""Prueba de integración: recorre un día completo de operación del restaurante.

Es la prueba básica de integración que exige el criterio de línea base:
participan los cinco módulos (autenticación, menú, pedidos, reservas y caja).
"""
from datetime import date, timedelta

from tests.conftest import CLAVE


def test_dia_completo_de_operacion(app, anonimo):
    # 1. Autenticación: un cliente se registra; el administrador se crea en base de datos.
    r = anonimo.post("/auth/registro", json={
        "nombre": "Carlos Pérez", "correo": "carlos@correo.com", "clave": CLAVE})
    assert r.status_code == 201

    from tests.conftest import _crear_usuario, _cliente_con_sesion
    _crear_usuario(app, "Ana Admin", "admin@sigr.test", "administrador")
    admin = _cliente_con_sesion(app, "admin@sigr.test")

    r = admin.post("/auth/registro", json={
        "nombre": "Mario Mesero", "correo": "mario@sigr.test", "clave": CLAVE, "rol": "mesero"})
    assert r.status_code == 201
    mesero = _cliente_con_sesion(app, "mario@sigr.test")
    cliente = _cliente_con_sesion(app, "carlos@correo.com")

    # 2. Menú: el administrador arma la carta y el cliente la consulta.
    cat = admin.post("/menu/categorias", json={"nombre": "Bebidas"}).get_json()
    jugo = admin.post("/menu/platos", json={
        "categoria_id": cat["id"], "nombre": "Jugo de lulo", "precio": 7000}).get_json()
    assert cliente.get("/menu").get_json()[0]["platos"][0]["nombre"] == "Jugo de lulo"

    # 3. Reservas: el cliente reserva una mesa para mañana.
    mesa = admin.post("/mesas", json={"numero": 3, "capacidad": 4}).get_json()
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = cliente.post("/reservas", json={
        "mesa_id": mesa["id"], "fecha": manana, "hora": "13:00", "personas": 3})
    assert r.status_code == 201

    # 4. Pedidos: el cliente pide y el mesero lleva el pedido hasta el cobro.
    r = cliente.post("/pedidos", json={
        "mesa_id": mesa["id"], "items": [{"plato_id": jugo["id"], "cantidad": 3}]})
    pedido = r.get_json()
    assert pedido["total"] == 21000
    for estado in ("en_preparacion", "listo", "entregado", "pagado"):
        assert mesero.patch(f"/pedidos/{pedido['id']}/estado",
                            json={"estado": estado}).status_code == 200

    # 5. Caja: el reporte refleja la venta y el cierre queda registrado.
    hoy = date.today().isoformat()
    reporte = admin.get(f"/caja/reporte?fecha={hoy}").get_json()
    assert reporte["total_ventas"] == 21000 and reporte["num_pedidos"] == 1
    assert reporte["platos_mas_vendidos"][0]["nombre"] == "Jugo de lulo"
    assert admin.post("/caja/cierre", json={"fecha": hoy}).status_code == 201
    assert admin.get("/caja/cierres").get_json()[0]["total_ventas"] == 21000
