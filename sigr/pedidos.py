"""Módulo de pedidos: registro y seguimiento del estado de cada pedido.

El seguimiento se resuelve consultando GET /pedidos/<id> (sondeo periódico).
La línea base no incluye notificaciones push ni WebSockets.
"""
from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db
from .util import ahora, cuerpo_json, entero, error, hoy

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")

ESTADOS = ("pendiente", "en_preparacion", "listo", "entregado", "pagado", "cancelado")

# Transiciones permitidas del ciclo de vida de un pedido.
TRANSICIONES = {
    "pendiente": ("en_preparacion", "cancelado"),
    "en_preparacion": ("listo", "cancelado"),
    "listo": ("entregado",),
    "entregado": ("pagado",),
    "pagado": (),
    "cancelado": (),
}

MAX_CANTIDAD = 20


def _armar(pedido):
    """Pedido con sus ítems, listo para serializar."""
    items = get_db().execute(
        "SELECT i.plato_id, p.nombre, i.cantidad, i.precio_unitario "
        "FROM pedido_items i JOIN platos p ON p.id = i.plato_id "
        "WHERE i.pedido_id = ? ORDER BY i.id", (pedido["id"],)
    ).fetchall()
    d = dict(pedido)
    d["items"] = [dict(i) for i in items]
    return d


def _puede_ver(pedido):
    return g.usuario["rol"] in ("mesero", "administrador") or pedido["usuario_id"] == g.usuario["id"]


@bp.post("")
@requiere_rol()
def crear():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    items = datos.get("items")
    if not isinstance(items, list) or not items:
        return error("El pedido debe incluir al menos un item", 422)

    db = get_db()
    mesa_id = datos.get("mesa_id")
    if mesa_id is not None:
        if entero(mesa_id, 1) is None or db.execute(
                "SELECT 1 FROM mesas WHERE id = ?", (mesa_id,)).fetchone() is None:
            return error("La mesa no existe", 422)

    lineas, total = [], 0
    for item in items:
        if not isinstance(item, dict):
            return error("Item invalido", 422)
        plato_id = entero(item.get("plato_id"), 1)
        cantidad = entero(item.get("cantidad"), 1, MAX_CANTIDAD)
        if plato_id is None or cantidad is None:
            return error(f"Item invalido: cantidad entre 1 y {MAX_CANTIDAD}", 422)
        plato = db.execute(
            "SELECT id, precio, disponible FROM platos WHERE id = ?", (plato_id,)).fetchone()
        if plato is None or not plato["disponible"]:
            return error(f"El plato {plato_id} no esta disponible", 422)
        lineas.append((plato_id, cantidad, plato["precio"]))
        total += cantidad * plato["precio"]

    momento = ahora()
    with db:  # una sola transacción: o se guarda todo el pedido o nada
        cur = db.execute(
            "INSERT INTO pedidos (usuario_id, mesa_id, estado, total, fecha, creado_en, actualizado_en) "
            "VALUES (?, ?, 'pendiente', ?, ?, ?, ?)",
            (g.usuario["id"], mesa_id, total, hoy(), momento, momento),
        )
        db.executemany(
            "INSERT INTO pedido_items (pedido_id, plato_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
            [(cur.lastrowid, p, c, pu) for p, c, pu in lineas],
        )
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_armar(pedido)), 201


@bp.get("")
@requiere_rol()
def listar():
    estado = request.args.get("estado")
    if estado is not None and estado not in ESTADOS:
        return error("Estado invalido", 422)
    consulta, params = "SELECT * FROM pedidos WHERE 1 = 1", []
    if g.usuario["rol"] == "cliente":
        consulta += " AND usuario_id = ?"
        params.append(g.usuario["id"])
    if estado:
        consulta += " AND estado = ?"
        params.append(estado)
    filas = get_db().execute(consulta + " ORDER BY id", params).fetchall()
    return jsonify([_armar(f) for f in filas])


@bp.get("/<int:pedido_id>")
@requiere_rol()
def ver(pedido_id):
    pedido = get_db().execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    # Se responde 404 también cuando el pedido es ajeno, para no revelar que existe.
    if pedido is None or not _puede_ver(pedido):
        return error("Pedido no encontrado", 404)
    return jsonify(_armar(pedido))


@bp.patch("/<int:pedido_id>/estado")
@requiere_rol("mesero", "administrador")
def cambiar_estado(pedido_id):
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    nuevo = datos.get("estado")
    if nuevo not in ESTADOS:
        return error("Estado invalido", 422)
    db = get_db()
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido is None:
        return error("Pedido no encontrado", 404)
    if nuevo not in TRANSICIONES[pedido["estado"]]:
        return error(f"No se puede pasar de {pedido['estado']} a {nuevo}", 409)
    db.execute("UPDATE pedidos SET estado = ?, actualizado_en = ? WHERE id = ?",
               (nuevo, ahora(), pedido_id))
    db.commit()
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return jsonify(_armar(pedido))
