"""Módulo de cierre de caja y reportes de ventas diarios.

Solo cuentan como venta los pedidos en estado "pagado". La fecha de un pedido
es la del día en que se creó.
"""
import re
import sqlite3
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db
from .util import ahora, cuerpo_json, error, hoy

bp = Blueprint("caja", __name__, url_prefix="/caja")

FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fecha(valor):
    """Valida AAAA-MM-DD y que no sea futura; devuelve la fecha o None."""
    if not isinstance(valor, str) or not FECHA_RE.match(valor):
        return None
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        return None
    return valor if valor <= hoy() else None


def _resumen(db, fecha):
    ventas = db.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(total), 0) AS total "
        "FROM pedidos WHERE fecha = ? AND estado = 'pagado'", (fecha,)).fetchone()
    top = db.execute(
        "SELECT p.nombre, SUM(i.cantidad) AS unidades, SUM(i.cantidad * i.precio_unitario) AS ingresos "
        "FROM pedido_items i JOIN pedidos d ON d.id = i.pedido_id JOIN platos p ON p.id = i.plato_id "
        "WHERE d.fecha = ? AND d.estado = 'pagado' "
        "GROUP BY p.id ORDER BY unidades DESC, p.nombre LIMIT 5", (fecha,)).fetchall()
    pendientes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE fecha = ? AND estado = 'entregado'", (fecha,)).fetchone()[0]
    n, total = ventas["n"], ventas["total"]
    return {
        "fecha": fecha,
        "num_pedidos": n,
        "total_ventas": total,
        "ticket_promedio": round(total / n) if n else 0,
        "pedidos_por_cobrar": pendientes,
        "platos_mas_vendidos": [dict(t) for t in top],
    }


@bp.get("/reporte")
@requiere_rol("administrador")
def reporte():
    fecha = _fecha(request.args.get("fecha", hoy()))
    if fecha is None:
        return error("Fecha invalida o futura (AAAA-MM-DD)", 422)
    return jsonify(_resumen(get_db(), fecha))


@bp.post("/cierre")
@requiere_rol("administrador")
def cerrar():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    fecha = _fecha(datos.get("fecha"))
    if fecha is None:
        return error("Fecha invalida o futura (AAAA-MM-DD)", 422)
    db = get_db()
    resumen = _resumen(db, fecha)
    # No se cierra el día mientras haya pedidos entregados sin cobrar.
    if resumen["pedidos_por_cobrar"]:
        return error("Hay pedidos entregados sin pagar; cobrelos antes de cerrar", 409,
                     pedidos_por_cobrar=resumen["pedidos_por_cobrar"])
    try:
        db.execute(
            "INSERT INTO cierres_caja (fecha, total_ventas, num_pedidos, cerrado_por, cerrado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (fecha, resumen["total_ventas"], resumen["num_pedidos"], g.usuario["id"], ahora()))
        db.commit()
    except sqlite3.IntegrityError:
        return error("La caja de esa fecha ya fue cerrada", 409)
    return jsonify(fecha=fecha, total_ventas=resumen["total_ventas"],
                   num_pedidos=resumen["num_pedidos"]), 201


@bp.get("/cierres")
@requiere_rol("administrador")
def cierres():
    filas = get_db().execute(
        "SELECT fecha, total_ventas, num_pedidos, cerrado_en FROM cierres_caja ORDER BY fecha DESC"
    ).fetchall()
    return jsonify([dict(f) for f in filas])
