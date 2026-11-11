"""Sistema Integral de Gestión de Restaurante (SIGR)."""
import os

import click
from flask import Flask, jsonify
from werkzeug.security import generate_password_hash

from . import db as base_datos
from .util import ahora, error

__version__ = "1.0.0"


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # En producción debe definirse SIGR_SECRET_KEY; sin ella se genera una
        # clave aleatoria que invalida las sesiones al reiniciar.
        SECRET_KEY=os.environ.get("SIGR_SECRET_KEY") or os.urandom(24).hex(),
        DATABASE=os.path.join(app.instance_path, "sigr.sqlite"),
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(base_datos.cerrar_db)

    from . import auth, menu, mesas, pedidos
    app.register_blueprint(auth.bp)
    app.register_blueprint(menu.bp)
    app.register_blueprint(mesas.bp)
    app.register_blueprint(pedidos.bp)

    @app.get("/salud")
    def salud():
        return jsonify(estado="ok", version=__version__)

    @app.errorhandler(404)
    def no_encontrado(_e):
        return error("Recurso no encontrado", 404)

    @app.errorhandler(405)
    def metodo_no_permitido(_e):
        return error("Metodo no permitido", 405)

    @app.errorhandler(500)
    def error_interno(_e):
        return error("Error interno del servidor", 500)

    _registrar_comandos(app)
    return app


def _registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas de la base de datos."""
        base_datos.iniciar_db()
        click.echo("Base de datos inicializada.")

    @app.cli.command("crear-admin")
    @click.argument("correo")
    @click.argument("nombre")
    @click.password_option()
    def crear_admin(correo, nombre, password):
        """Crea una cuenta de administrador (la clave se pide por consola)."""
        db = base_datos.get_db()
        db.execute(
            "INSERT INTO usuarios (nombre, correo, clave_hash, rol, creado_en) "
            "VALUES (?, ?, ?, 'administrador', ?)",
            (nombre, correo.strip().lower(), generate_password_hash(password), ahora()),
        )
        db.commit()
        click.echo("Administrador creado.")
