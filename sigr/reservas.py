"""Módulo de reservas por fecha y hora."""
import re
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db
from .util import ahora, cuerpo_json, entero, error, hoy

bp = Blueprint("reservas", __name__, url_prefix="/reservas")

HORA_PRIMERA = 11 * 60      # 11:00, primera hora reservable (en minutos)
HORA_ULTIMA = 21 * 60       # 21:00, última hora de inicio reservable
DURACION = 120              # cada reserva ocupa la mesa 2 horas

FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HORA_RE = re.compile(r"^\d{2}:\d{2}$")


def _fecha_valida(valor):
    if not isinstance(valor, str) or not FECHA_RE.match(valor):
        return None
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        return None
    return valor


def _minutos(hora):
    """'HH:MM' -> minutos desde medianoche, o None si no es una hora real."""
    if not isinstance(hora, str) or not HORA_RE.match(hora):
        return None
    h, m = int(hora[:2]), int(hora[3:])
    return h * 60 + m if h < 24 and m < 60 else None


def _publica(fila):
    return {k: fila[k] for k in ("id", "mesa_id", "fecha", "hora", "personas", "estado")}


@bp.post("")
@requiere_rol()
def crear():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)

    mesa_id = entero(datos.get("mesa_id"), 1)
    personas = entero(datos.get("personas"), 1)
    fecha = _fecha_valida(datos.get("fecha"))
    inicio = _minutos(datos.get("hora"))

    errores = {}
    if mesa_id is None:
        errores["mesa_id"] = "Mesa obligatoria"
    if personas is None:
        errores["personas"] = "Numero de personas obligatorio"
    if fecha is None:
        errores["fecha"] = "Fecha invalida (AAAA-MM-DD)"
    elif fecha < hoy():
        errores["fecha"] = "No se puede reservar en una fecha pasada"
    if inicio is None:
        errores["hora"] = "Hora invalida (HH:MM)"
    elif not HORA_PRIMERA <= inicio <= HORA_ULTIMA:
        errores["hora"] = "Horario de reservas: 11:00 a 21:00"
    if errores:
        return error("Datos invalidos", 422, errores=errores)

    db = get_db()
    mesa = db.execute("SELECT id, capacidad FROM mesas WHERE id = ?", (mesa_id,)).fetchone()
    if mesa is None:
        return error("La mesa no existe", 422)
    if personas > mesa["capacidad"]:
        return error(f"La mesa tiene capacidad para {mesa['capacidad']} personas", 422)

    # Una reserva choca con otra de la misma mesa y fecha si se solapan sus 2 horas.
    existentes = db.execute(
        "SELECT hora FROM reservas WHERE mesa_id = ? AND fecha = ? AND estado = 'activa'",
        (mesa_id, fecha)).fetchall()
    for fila in existentes:
        if abs(_minutos(fila["hora"]) - inicio) < DURACION:
            return error("La mesa ya esta reservada en ese horario", 409)

    hora = f"{inicio // 60:02d}:{inicio % 60:02d}"
    cur = db.execute(
        "INSERT INTO reservas (usuario_id, mesa_id, fecha, hora, personas, estado, creado_en) "
        "VALUES (?, ?, ?, ?, ?, 'activa', ?)",
        (g.usuario["id"], mesa_id, fecha, hora, personas, ahora()))
    db.commit()
    fila = db.execute("SELECT * FROM reservas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_publica(fila)), 201


@bp.get("")
@requiere_rol()
def listar():
    fecha = request.args.get("fecha")
    if fecha is not None and _fecha_valida(fecha) is None:
        return error("Fecha invalida (AAAA-MM-DD)", 422)
    consulta, params = "SELECT * FROM reservas WHERE 1 = 1", []
    if g.usuario["rol"] == "cliente":
        consulta += " AND usuario_id = ?"
        params.append(g.usuario["id"])
    if fecha:
        consulta += " AND fecha = ?"
        params.append(fecha)
    filas = get_db().execute(consulta + " ORDER BY fecha, hora", params).fetchall()
    return jsonify([_publica(f) for f in filas])


@bp.delete("/<int:reserva_id>")
@requiere_rol()
def cancelar(reserva_id):
    db = get_db()
    fila = db.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    es_personal = g.usuario["rol"] in ("mesero", "administrador")
    if fila is None or (not es_personal and fila["usuario_id"] != g.usuario["id"]):
        return error("Reserva no encontrada", 404)
    if fila["estado"] == "cancelada":
        return error("La reserva ya estaba cancelada", 409)
    db.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
    db.commit()
    fila = db.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    return jsonify(_publica(fila))
