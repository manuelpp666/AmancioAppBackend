"""Funciones de ayuda que usan varios services: leer y validar los datos que
llegan en el JSON, convertir respuestas a JSON y manejar nombres de usuario.

Cada validador recibe el dict `datos` (el JSON de la petición) y el nombre del
campo. Si el valor no es válido, lanza ApiError(400) con un mensaje claro.
"""
import datetime as dt
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
    """Cómo se convierten a JSON los tipos que llegan de MySQL:
    - DATE / DATETIME → texto ISO ("2026-03-09", "2026-03-09T07:30:00")
    - TIME            → "07:30" (PyMySQL lo entrega como timedelta)
    - DECIMAL         → número (14.5) en vez de texto ("14.50")
    """
    ensure_ascii = False   # deja las tildes y la ñ tal cual (no como ñ)

    @staticmethod
    def default(o):
        if isinstance(o, (dt.datetime, dt.date, dt.time)):
            return o.isoformat()
        if isinstance(o, dt.timedelta):
            return hora_texto(o)
        if isinstance(o, Decimal):
            return float(o)
        return DefaultJSONProvider.default(o)


def hora_texto(duracion: dt.timedelta) -> str:
    """Convierte una hora de MySQL (timedelta) a texto "HH:MM"."""
    minutos = int(duracion.total_seconds()) // 60
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


# --- Leer el JSON de la petición ---------------------------------------------

def json_requerido() -> dict:
    """Devuelve el cuerpo JSON de la petición, o error 400 si no se envió un objeto JSON."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ApiError(400, "Se esperaba un cuerpo JSON")
    return datos


# --- Validadores --------------------------------------------------------------

def texto(datos: dict, campo: str, *, minimo: int = 1, maximo: int | None = None,
          requerido: bool = True, strip: bool = True):
    """Lee un campo de texto y valida su largo.

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


def entero(datos: dict, campo: str, *, minimo: int, maximo: int) -> int:
    """Lee un campo numérico entero (obligatorio) y valida que esté en el rango."""
    valor = datos.get(campo)
    if valor is None:
        raise ApiError(400, f"Falta el campo '{campo}'")
    # bool se excluye porque en Python True/False también cuentan como números.
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ApiError(400, f"El campo '{campo}' debe ser un número entero")
    if not minimo <= valor <= maximo:
        raise ApiError(400, f"El campo '{campo}' debe estar entre {minimo} y {maximo}")
    return valor


def numero(datos: dict, campo: str, *, minimo: float, maximo: float) -> float:
    """Lee un número (entero o con decimales, obligatorio), ej. una nota de 0 a 20.
    Se redondea a 2 decimales, como se guarda en MySQL."""
    valor = datos.get(campo)
    if valor is None:
        raise ApiError(400, f"Falta el campo '{campo}'")
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        raise ApiError(400, f"El campo '{campo}' debe ser un número")
    if not minimo <= valor <= maximo:
        raise ApiError(400, f"El campo '{campo}' debe estar entre {minimo:g} y {maximo:g}")
    return round(float(valor), 2)


def fecha(datos: dict, campo: str, *, requerido: bool = True):
    """Lee una fecha "AAAA-MM-DD" y la devuelve como date (o None si es opcional y falta)."""
    valor = texto(datos, campo, minimo=1, maximo=30, requerido=requerido)
    if valor is None:
        return None
    try:
        return dt.date.fromisoformat(valor)
    except ValueError:
        raise ApiError(400, f"El campo '{campo}' debe tener el formato AAAA-MM-DD")


def fecha_hora(datos: dict, campo: str) -> dt.datetime:
    """Lee una fecha con hora "AAAA-MM-DDTHH:MM" (obligatoria) y la devuelve como datetime."""
    valor = texto(datos, campo, minimo=1, maximo=30)
    try:
        return dt.datetime.fromisoformat(valor)
    except ValueError:
        raise ApiError(400, f"El campo '{campo}' debe tener el formato AAAA-MM-DDTHH:MM")


def enlace(datos: dict, campo: str, *, requerido: bool = False, maximo: int = 500):
    """Lee un enlace web (http o https). Opcional por defecto: devuelve None si falta."""
    valor = texto(datos, campo, minimo=0, maximo=maximo, requerido=requerido) or None
    if valor is None and requerido:
        raise ApiError(400, f"Falta el campo '{campo}'")
    if valor and not valor.startswith(("http://", "https://")):
        raise ApiError(400, f"El campo '{campo}' debe empezar con http:// o https://")
    return valor


def fecha_de_query(nombre: str = "fecha"):
    """Lee una fecha opcional de la URL (?fecha=2026-10-13). None si no viene."""
    valor = request.args.get(nombre)
    if not valor:
        return None
    try:
        return dt.date.fromisoformat(valor)
    except ValueError:
        raise ApiError(400, f"El parámetro '{nombre}' debe tener el formato AAAA-MM-DD")


# --- Usuarios -----------------------------------------------------------------

def extraer_dni(username: str) -> str:
    """Saca el DNI del nombre de usuario: 'ALU-12345678' → '12345678'.
    Si no tiene un prefijo conocido, devuelve el username tal cual."""
    if not username:
        return ""
    prefijo, guion, resto = username.partition("-")
    if guion and prefijo.upper() in _PREFIJOS:
        return resto
    return username
