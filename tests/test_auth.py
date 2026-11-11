"""Pruebas del módulo de autenticación y control de acceso."""
from tests.conftest import CLAVE

REGISTRO = {"nombre": "Laura Ríos", "correo": "laura@correo.com", "clave": CLAVE}


def test_salud(anonimo):
    r = anonimo.get("/salud")
    assert r.status_code == 200
    assert r.get_json()["estado"] == "ok"


def test_registro_crea_cliente_por_defecto(anonimo):
    r = anonimo.post("/auth/registro", json=REGISTRO)
    assert r.status_code == 201
    datos = r.get_json()
    assert datos["rol"] == "cliente"
    assert "clave" not in datos and "clave_hash" not in datos


def test_registro_normaliza_correo_y_rechaza_duplicado(anonimo):
    anonimo.post("/auth/registro", json=REGISTRO)
    r = anonimo.post("/auth/registro", json={**REGISTRO, "correo": "  LAURA@Correo.COM "})
    assert r.status_code == 409


def test_registro_valida_campos(anonimo):
    r = anonimo.post("/auth/registro", json={"nombre": "Al", "correo": "x", "clave": "corta"})
    assert r.status_code == 422
    assert set(r.get_json()["errores"]) == {"nombre", "correo", "clave"}


def test_registro_exige_json(anonimo):
    assert anonimo.post("/auth/registro", data="no es json").status_code == 400


def test_anonimo_no_puede_crear_personal(anonimo):
    r = anonimo.post("/auth/registro", json={**REGISTRO, "rol": "administrador"})
    assert r.status_code == 403


def test_administrador_puede_crear_mesero(admin):
    r = admin.post("/auth/registro", json={**REGISTRO, "rol": "mesero"})
    assert r.status_code == 201
    assert r.get_json()["rol"] == "mesero"


def test_login_y_yo(anonimo):
    anonimo.post("/auth/registro", json=REGISTRO)
    r = anonimo.post("/auth/login", json={"correo": "laura@correo.com", "clave": CLAVE})
    assert r.status_code == 200
    assert anonimo.get("/auth/yo").get_json()["correo"] == "laura@correo.com"


def test_login_con_clave_incorrecta(anonimo):
    anonimo.post("/auth/registro", json=REGISTRO)
    r = anonimo.post("/auth/login", json={"correo": "laura@correo.com", "clave": "otra-clave-123"})
    assert r.status_code == 401


def test_logout_cierra_la_sesion(cliente):
    assert cliente.get("/auth/yo").status_code == 200
    assert cliente.post("/auth/logout").status_code == 204
    assert cliente.get("/auth/yo").status_code == 401


def test_yo_sin_sesion(anonimo):
    assert anonimo.get("/auth/yo").status_code == 401
