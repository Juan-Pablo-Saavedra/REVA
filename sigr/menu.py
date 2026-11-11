"""Módulo de menú digital: CRUD de categorías y platos."""
import sqlite3

from flask import Blueprint, jsonify

from .auth import requiere_rol
from .db import get_db
from .util import cuerpo_json, entero, error, texto

bp = Blueprint("menu", __name__, url_prefix="/menu")


def _plato(fila):
    d = dict(fila)
    d["disponible"] = bool(d["disponible"])
    return d


@bp.get("")
def ver_menu():
    """Menú público: categorías con sus platos disponibles."""
    db = get_db()
    resultado = []
    for cat in db.execute("SELECT id, nombre FROM categorias ORDER BY nombre"):
        platos = db.execute(
            "SELECT id, nombre, descripcion, precio FROM platos "
            "WHERE categoria_id = ? AND disponible = 1 ORDER BY nombre", (cat["id"],)
        ).fetchall()
        resultado.append({"id": cat["id"], "nombre": cat["nombre"],
                          "platos": [dict(p) for p in platos]})
    return jsonify(resultado)


# --- Categorías -----------------------------------------------------------

@bp.post("/categorias")
@requiere_rol("administrador")
def crear_categoria():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    nombre = texto(datos.get("nombre"), 2, 60)
    if nombre is None:
        return error("Datos invalidos", 422, errores={"nombre": "Nombre obligatorio (2 a 60 caracteres)"})
    db = get_db()
    try:
        cur = db.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        db.commit()
    except sqlite3.IntegrityError:
        return error("La categoria ya existe", 409)
    return jsonify(id=cur.lastrowid, nombre=nombre), 201


@bp.put("/categorias/<int:cat_id>")
@requiere_rol("administrador")
def renombrar_categoria(cat_id):
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    nombre = texto(datos.get("nombre"), 2, 60)
    if nombre is None:
        return error("Datos invalidos", 422, errores={"nombre": "Nombre obligatorio (2 a 60 caracteres)"})
    db = get_db()
    if db.execute("SELECT 1 FROM categorias WHERE id = ?", (cat_id,)).fetchone() is None:
        return error("Categoria no encontrada", 404)
    try:
        db.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nombre, cat_id))
        db.commit()
    except sqlite3.IntegrityError:
        return error("La categoria ya existe", 409)
    return jsonify(id=cat_id, nombre=nombre)


@bp.delete("/categorias/<int:cat_id>")
@requiere_rol("administrador")
def eliminar_categoria(cat_id):
    db = get_db()
    if db.execute("SELECT 1 FROM categorias WHERE id = ?", (cat_id,)).fetchone() is None:
        return error("Categoria no encontrada", 404)
    if db.execute("SELECT 1 FROM platos WHERE categoria_id = ?", (cat_id,)).fetchone():
        return error("No se puede eliminar una categoria que tiene platos", 409)
    db.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
    db.commit()
    return "", 204


# --- Platos ---------------------------------------------------------------

def _validar_plato(datos, parcial=False):
    """Devuelve (valores, errores). Con parcial=True solo valida lo enviado."""
    valores, errores = {}, {}
    if not parcial or "nombre" in datos:
        v = texto(datos.get("nombre"), 2, 80)
        if v is None:
            errores["nombre"] = "Nombre obligatorio (2 a 80 caracteres)"
        else:
            valores["nombre"] = v
    if not parcial or "precio" in datos:
        v = entero(datos.get("precio"), 1, 10_000_000)
        if v is None:
            errores["precio"] = "El precio debe ser un entero mayor que 0"
        else:
            valores["precio"] = v
    if "descripcion" in datos:
        v = datos["descripcion"]
        if not isinstance(v, str) or len(v) > 300:
            errores["descripcion"] = "Descripcion de hasta 300 caracteres"
        else:
            valores["descripcion"] = v.strip()
    if "disponible" in datos:
        if not isinstance(datos["disponible"], bool):
            errores["disponible"] = "Debe ser verdadero o falso"
        else:
            valores["disponible"] = int(datos["disponible"])
    if "categoria_id" in datos or not parcial:
        v = entero(datos.get("categoria_id"), 1)
        if v is None:
            errores["categoria_id"] = "Categoria obligatoria"
        else:
            valores["categoria_id"] = v
    return valores, errores


@bp.post("/platos")
@requiere_rol("administrador")
def crear_plato():
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    valores, errores = _validar_plato(datos)
    if errores:
        return error("Datos invalidos", 422, errores=errores)
    db = get_db()
    if db.execute("SELECT 1 FROM categorias WHERE id = ?", (valores["categoria_id"],)).fetchone() is None:
        return error("Datos invalidos", 422, errores={"categoria_id": "La categoria no existe"})
    try:
        cur = db.execute(
            "INSERT INTO platos (categoria_id, nombre, descripcion, precio, disponible) "
            "VALUES (?, ?, ?, ?, ?)",
            (valores["categoria_id"], valores["nombre"], valores.get("descripcion", ""),
             valores["precio"], valores.get("disponible", 1)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("Ya existe un plato con ese nombre en la categoria", 409)
    fila = db.execute("SELECT * FROM platos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(_plato(fila)), 201


@bp.get("/platos/<int:plato_id>")
def ver_plato(plato_id):
    fila = get_db().execute("SELECT * FROM platos WHERE id = ?", (plato_id,)).fetchone()
    if fila is None:
        return error("Plato no encontrado", 404)
    return jsonify(_plato(fila))


@bp.put("/platos/<int:plato_id>")
@requiere_rol("administrador")
def actualizar_plato(plato_id):
    datos = cuerpo_json()
    if datos is None:
        return error("El cuerpo debe ser JSON", 400)
    db = get_db()
    if db.execute("SELECT 1 FROM platos WHERE id = ?", (plato_id,)).fetchone() is None:
        return error("Plato no encontrado", 404)
    valores, errores = _validar_plato(datos, parcial=True)
    if errores:
        return error("Datos invalidos", 422, errores=errores)
    if not valores:
        return error("No se envio ningun campo para actualizar", 422)
    if "categoria_id" in valores and db.execute(
            "SELECT 1 FROM categorias WHERE id = ?", (valores["categoria_id"],)).fetchone() is None:
        return error("Datos invalidos", 422, errores={"categoria_id": "La categoria no existe"})
    asignaciones = ", ".join(f"{campo} = ?" for campo in valores)  # campos validados arriba
    try:
        db.execute(f"UPDATE platos SET {asignaciones} WHERE id = ?", (*valores.values(), plato_id))
        db.commit()
    except sqlite3.IntegrityError:
        return error("Ya existe un plato con ese nombre en la categoria", 409)
    fila = db.execute("SELECT * FROM platos WHERE id = ?", (plato_id,)).fetchone()
    return jsonify(_plato(fila))


@bp.delete("/platos/<int:plato_id>")
@requiere_rol("administrador")
def eliminar_plato(plato_id):
    db = get_db()
    if db.execute("SELECT 1 FROM platos WHERE id = ?", (plato_id,)).fetchone() is None:
        return error("Plato no encontrado", 404)
    try:
        db.execute("DELETE FROM platos WHERE id = ?", (plato_id,))
        db.commit()
    except sqlite3.IntegrityError:
        # El plato ya figura en pedidos: se conserva el historial y se marca no disponible.
        db.execute("UPDATE platos SET disponible = 0 WHERE id = ?", (plato_id,))
        db.commit()
        return error("El plato tiene pedidos asociados; se marco como no disponible", 409)
    return "", 204
