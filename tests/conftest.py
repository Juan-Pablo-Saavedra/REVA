import pytest
from werkzeug.security import generate_password_hash

from sigr import create_app
from sigr.db import get_db, iniciar_db
from sigr.util import ahora

CLAVE = "clave-segura-123"


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "clave-solo-para-pruebas",
        "DATABASE": str(tmp_path / "prueba.sqlite"),
    })
    with app.app_context():
        iniciar_db()
    return app


def _crear_usuario(app, nombre, correo, rol):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nombre, correo, clave_hash, rol, creado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (nombre, correo, generate_password_hash(CLAVE), rol, ahora()),
        )
        db.commit()


def _cliente_con_sesion(app, correo):
    cliente = app.test_client()
    r = cliente.post("/auth/login", json={"correo": correo, "clave": CLAVE})
    assert r.status_code == 200, r.get_json()
    return cliente


@pytest.fixture
def anonimo(app):
    return app.test_client()


@pytest.fixture
def admin(app):
    _crear_usuario(app, "Ana Admin", "admin@sigr.test", "administrador")
    return _cliente_con_sesion(app, "admin@sigr.test")


@pytest.fixture
def mesero(app):
    _crear_usuario(app, "Mario Mesero", "mesero@sigr.test", "mesero")
    return _cliente_con_sesion(app, "mesero@sigr.test")


@pytest.fixture
def cliente(app):
    _crear_usuario(app, "Clara Cliente", "cliente@sigr.test", "cliente")
    return _cliente_con_sesion(app, "cliente@sigr.test")


@pytest.fixture
def carta(admin):
    """Carga una categoría con dos platos usando la API de administración."""
    cat = admin.post("/menu/categorias", json={"nombre": "Platos fuertes"}).get_json()
    bandeja = admin.post("/menu/platos", json={
        "categoria_id": cat["id"], "nombre": "Bandeja paisa", "precio": 32000}).get_json()
    sopa = admin.post("/menu/platos", json={
        "categoria_id": cat["id"], "nombre": "Sancocho", "precio": 25000}).get_json()
    return {"categoria": cat, "bandeja": bandeja, "sopa": sopa}
