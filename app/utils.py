"""Funciones de ayuda que usan varias rutas: leer y validar el JSON de la
petición, convertir modelos a diccionario y manejar los nombres de usuario."""
import datetime as dt
import enum
import re
from decimal import Decimal

from flask import request
from flask.json.provider import DefaultJSONProvider

from app.errors import ApiError

# Formato mínimo de un correo: algo@algo.algo
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Prefijos de los nombres de usuario del colegio: ALU-12345678, DOC-12345678...
_PREFIJOS = {"ADM", "DOC", "ALU", "AUX", "PSI"}


class ProveedorJSON(DefaultJSONProvider):
    """Cómo se convierten a JSON los tipos que Flask no maneja bien por defecto:
    - fechas  → texto ISO ("2026-03-09"), fácil de leer desde la app
    - Decimal → número (14.5) en vez de texto ("14.50")
    - Enum    → su valor
    """
    ensure_ascii = False   # deja las tildes y la ñ tal cual (no como ñ)

    @staticmethod
    def default(o):
        if isinstance(o, (dt.datetime, dt.date, dt.time)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, enum.Enum):
            return o.value
        return DefaultJSONProvider.default(o)


def a_dict(modelo) -> dict:
    """Convierte una fila de la base (modelo SQLAlchemy) en diccionario {columna: valor}."""
    return {columna.key: getattr(modelo, columna.key) for columna in modelo.__table__.columns}


def json_requerido() -> dict:
    """Devuelve el cuerpo JSON de la petición, o error 400 si no se envió un objeto JSON."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ApiError(400, "Se esperaba un cuerpo JSON")
    return datos


def texto(datos: dict, campo: str, *, minimo: int = 1, maximo: int | None = None,
          requerido: bool = True, strip: bool = True):
    """Lee un campo de texto del JSON y valida su largo.

    - Si falta y es requerido → error 400. Si falta y es opcional → devuelve None.
    - strip=True quita los espacios del inicio y del final (no se usa en contraseñas).
    """
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
    """Saca el DNI del nombre de usuario: 'ALU-12345678' → '12345678'.
    Si no tiene un prefijo conocido, devuelve el username tal cual."""
    if not username:
        return ""
    prefijo, guion, resto = username.partition("-")
    if guion and prefijo.upper() in _PREFIJOS:
        return resto
    return username
