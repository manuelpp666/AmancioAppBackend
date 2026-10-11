"""Utilidades comunes: validación de JSON, serialización y nombres de usuario."""
import datetime as dt
import enum
import re
from decimal import Decimal

from flask import request
from flask.json.provider import DefaultJSONProvider

from app.errors import ApiError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PREFIJOS = {"ADM", "DOC", "ALU", "AUX", "PSI"}


class ProveedorJSON(DefaultJSONProvider):
    """Fechas en ISO 8601 y Decimal como número (Flask los manda por defecto como
    texto RFC 822 y como cadena, que es incómodo para la app)."""
    ensure_ascii = False

    @staticmethod
    def default(o):
        if isinstance(o, (dt.datetime, dt.date, dt.time)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, enum.Enum):
            return o.value
        return DefaultJSONProvider.default(o)


def a_dict(obj, excluir=()) -> dict:
    """Todas las columnas de un modelo SQLAlchemy como diccionario."""
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns if c.key not in excluir}


def json_requerido() -> dict:
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ApiError(400, "Se esperaba un cuerpo JSON")
    return datos


def texto(datos: dict, campo: str, *, minimo: int = 1, maximo: int | None = None,
          requerido: bool = True, strip: bool = True):
    """Lee un campo de texto validando longitud. Devuelve None si es opcional y falta."""
    valor = datos.get(campo)
    if valor is None:
        if requerido:
            raise ApiError(400, f"Falta el campo '{campo}'")
        return None
    if not isinstance(valor, str):
        raise ApiError(400, f"El campo '{campo}' debe ser texto")
    if strip:
        valor = valor.strip()
    if len(valor) < minimo:
        raise ApiError(400, f"El campo '{campo}' debe tener al menos {minimo} caracteres")
    if maximo is not None and len(valor) > maximo:
        raise ApiError(400, f"El campo '{campo}' admite como máximo {maximo} caracteres")
    return valor


def extraer_dni(username: str) -> str:
    """DNI de un username con prefijo ('ALU-12345678' -> '12345678')."""
    if not username:
        return ""
    prefijo, sep, resto = username.partition("-")
    return resto if sep and prefijo.upper() in _PREFIJOS else username
