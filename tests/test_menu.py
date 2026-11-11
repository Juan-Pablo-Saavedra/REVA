"""Pruebas del módulo de menú digital (CRUD de categorías y platos)."""


def test_menu_publico_vacio(anonimo):
    r = anonimo.get("/menu")
    assert r.status_code == 200 and r.get_json() == []


def test_crear_categoria_requiere_administrador(anonimo, cliente, mesero):
    cuerpo = {"nombre": "Postres"}
    assert anonimo.post("/menu/categorias", json=cuerpo).status_code == 401
    assert cliente.post("/menu/categorias", json=cuerpo).status_code == 403
    assert mesero.post("/menu/categorias", json=cuerpo).status_code == 403


def test_categoria_duplicada(admin):
    assert admin.post("/menu/categorias", json={"nombre": "Postres"}).status_code == 201
    assert admin.post("/menu/categorias", json={"nombre": "Postres"}).status_code == 409


def test_categoria_nombre_invalido(admin):
    assert admin.post("/menu/categorias", json={"nombre": "P"}).status_code == 422
    assert admin.post("/menu/categorias", json={"nombre": 123}).status_code == 422


def test_renombrar_categoria(admin, carta):
    cid = carta["categoria"]["id"]
    r = admin.put(f"/menu/categorias/{cid}", json={"nombre": "Fuertes"})
    assert r.status_code == 200 and r.get_json()["nombre"] == "Fuertes"
    assert admin.put("/menu/categorias/9999", json={"nombre": "Otra"}).status_code == 404


def test_no_se_elimina_categoria_con_platos(admin, carta):
    cid = carta["categoria"]["id"]
    assert admin.delete(f"/menu/categorias/{cid}").status_code == 409


def test_eliminar_categoria_vacia(admin):
    cid = admin.post("/menu/categorias", json={"nombre": "Bebidas"}).get_json()["id"]
    assert admin.delete(f"/menu/categorias/{cid}").status_code == 204
    assert admin.delete(f"/menu/categorias/{cid}").status_code == 404


def test_crear_y_consultar_plato(admin, carta, anonimo):
    plato = carta["bandeja"]
    assert plato["disponible"] is True and plato["precio"] == 32000
    r = anonimo.get(f"/menu/platos/{plato['id']}")
    assert r.status_code == 200 and r.get_json()["nombre"] == "Bandeja paisa"


def test_plato_invalido(admin, carta):
    cid = carta["categoria"]["id"]
    base = {"categoria_id": cid, "nombre": "Ajiaco", "precio": 20000}
    for cambio in ({"precio": 0}, {"precio": -5}, {"precio": "caro"}, {"precio": 10.5},
                   {"precio": True}, {"nombre": "A"}, {"categoria_id": 9999}):
        r = admin.post("/menu/platos", json={**base, **cambio})
        assert r.status_code == 422, cambio


def test_plato_duplicado_en_la_categoria(admin, carta):
    r = admin.post("/menu/platos", json={
        "categoria_id": carta["categoria"]["id"], "nombre": "Sancocho", "precio": 1000})
    assert r.status_code == 409


def test_actualizar_plato_parcial(admin, carta):
    pid = carta["sopa"]["id"]
    r = admin.put(f"/menu/platos/{pid}", json={"precio": 27000, "disponible": False})
    assert r.status_code == 200
    assert r.get_json()["precio"] == 27000 and r.get_json()["disponible"] is False
    assert admin.put(f"/menu/platos/{pid}", json={}).status_code == 422


def test_menu_publico_oculta_platos_no_disponibles(admin, carta, anonimo):
    admin.put(f"/menu/platos/{carta['sopa']['id']}", json={"disponible": False})
    menu = anonimo.get("/menu").get_json()
    nombres = [p["nombre"] for c in menu for p in c["platos"]]
    assert nombres == ["Bandeja paisa"]


def test_eliminar_plato(admin, carta):
    pid = carta["bandeja"]["id"]
    assert admin.delete(f"/menu/platos/{pid}").status_code == 204
    assert admin.get(f"/menu/platos/{pid}").status_code == 404
