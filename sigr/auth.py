"""Módulo de autenticación y control de acceso por roles."""
import functools
import re
import sqlite3

from flask import Blueprint, g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .util import ahora, cuerpo_json, error, texto

bp = Blueprint("auth", __name__, url_prefix="/auth")

ROLES = ("cliente", "mesero", "administrador")
CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.before_app_request
def cargar_usuario():
    """Deja en g.usuario al usuario de la sesión (o None)."""
    uid = session.get("usuario_id")
    g.usuario = None
    if uid is not None:
        g.usuario = get_db().execute(
            "SELECT id, nombre, correo, rol FROM usuarios WHERE id = ?", (uid,)
        ).fetchone()


def requiere_rol(*roles):
    """Exige sesión iniciada y, si se indican roles, que el usuario tenga uno."""
    def decorador(vista):
        @functools.wraps(vista)
        def envoltura(*args, **kwargs):
            if g.usuario is None:
                return error("Autenticacion requerida", 401)
            if roles and g.usuario["rol"] not in roles:
                return error("No tiene permiso para esta accion", 403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def _publico(fila):
    return {k: fila[k] for k in ("id", "nombre", "correo", "rol")}


@bp.post("/registro")
def registro():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)

    nombre = texto(datos.get("nombre"), 3, 80)
    correo = datos.get("correo")
    correo = correo.strip().lower() if isinstance(correo, str) else None
    clave = datos.get("clave")
    rol = datos.get("rol", "cliente")

    errores = {}
    if nombre is None:
        errores["nombre"] = "El nombre es obligatorio (minimo 3 caracteres)"
    if correo is None or not CORREO_RE.match(correo):
        errores["correo"] = "Correo invalido"
    if not isinstance(clave, str) or len(clave) < 8:
        errores["clave"] = "La clave debe tener al menos 8 caracteres"
    if rol not in ROLES:
        errores["rol"] = "Rol invalido"
    if errores:
        return error("Datos invalidos", 422, errores=errores)

    # Solo un administrador autenticado puede crear cuentas de personal.
    if rol != "cliente" and (g.usuario is None or g.usuario["rol"] != "administrador"):
        return error("Solo un administrador puede crear este rol", 403)

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO usuarios (nombre, correo, clave_hash, rol, creado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (nombre, correo, generate_password_hash(clave), rol, ahora()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("El correo ya esta registrado", 409)
    fila = db.execute("SELECT * FROM usuarios WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(_publico(fila)), 201


@bp.post("/login")
def login():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    correo = datos.get("correo")
    clave = datos.get("clave")
    fila = None
    if isinstance(correo, str) and isinstance(clave, str):
        fila = get_db().execute(
            "SELECT * FROM usuarios WHERE correo = ?", (correo.strip().lower(),)
        ).fetchone()
    # Mismo mensaje si falla el correo o la clave: no se revela cuál fue.
    if fila is None or not check_password_hash(fila["clave_hash"], clave):
        return error("Credenciales invalidas", 401)
    session.clear()
    session["usuario_id"] = fila["id"]
    return jsonify(_publico(fila))


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/yo")
@requiere_rol()
def yo():
    return jsonify(dict(g.usuario))
