"""Acceso a la base de datos SQLite."""
import sqlite3
from pathlib import Path

from flask import current_app, g

ESQUEMA = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


def get_db():
    """Conexión de la petición actual (se crea una vez por petición)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def cerrar_db(_excepcion=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def iniciar_db():
    """Crea las tablas a partir de database/schema.sql."""
    db = get_db()
    db.executescript(ESQUEMA.read_text(encoding="utf-8"))
    db.commit()
