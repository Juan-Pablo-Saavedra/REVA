"""Gestión de mesas del restaurante (soporte para pedidos y reservas)."""
import sqlite3

from flask import Blueprint, jsonify

from .auth import requiere_rol
from .db import get_db
from .util import cuerpo_json, entero, error

bp = Blueprint("mesas", __name__, url_prefix="/mesas")


@bp.get("")
@requiere_rol()
def listar():
    filas = get_db().execute("SELECT id, numero, capacidad FROM mesas ORDER BY numero").fetchall()
    return jsonify([dict(f) for f in filas])


@bp.post("")
@requiere_rol("administrador")
def crear():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    numero = entero(datos.get("numero"), 1, 999)
    capacidad = entero(datos.get("capacidad"), 1, 20)
    errores = {}
    if numero is None:
        errores["numero"] = "Numero de mesa entre 1 y 999"
    if capacidad is None:
        errores["capacidad"] = "Capacidad entre 1 y 20"
    if errores:
        return error("Datos invalidos", 422, errores=errores)
    db = get_db()
    try:
        cur = db.execute("INSERT INTO mesas (numero, capacidad) VALUES (?, ?)", (numero, capacidad))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Ya existe una mesa con ese numero", 409)
    return jsonify(id=cur.lastrowid, numero=numero, capacidad=capacidad), 201
