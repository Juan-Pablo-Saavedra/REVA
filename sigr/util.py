"""Utilidades compartidas por todos los módulos del SIGR."""
from datetime import date, datetime

from flask import jsonify, request


def hoy():
    """Fecha actual en formato AAAA-MM-DD."""
    return date.today().isoformat()


def ahora():
    """Marca de tiempo actual en formato ISO 8601 sin fracciones."""
    return datetime.now().isoformat(timespec="seconds")


def error(mensaje, codigo, **extra):
    """Respuesta de error uniforme: {"error": "..."} con el código HTTP dado."""
    return jsonify(error=mensaje, **extra), codigo


def cuerpo_json():
    """Devuelve el cuerpo JSON si es un objeto; en otro caso, None."""
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


def texto(valor, minimo, maximo):
    """Devuelve el texto recortado si su longitud es válida; si no, None."""
    if not isinstance(valor, str):
        return None
    valor = valor.strip()
    return valor if minimo <= len(valor) <= maximo else None


def entero(valor, minimo=None, maximo=None):
    """Devuelve el entero si es int (no bool) y está en rango; si no, None."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None
    if minimo is not None and valor < minimo:
        return None
    if maximo is not None and valor > maximo:
        return None
    return valor
