"""Configuración leída de variables de entorno (.env en local, panel en Render)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _entero(nombre: str, defecto: int) -> int:
    try:
        return int((os.getenv(nombre) or "").strip() or defecto)
    except ValueError:
        return defecto


# --- Base de datos MySQL (la misma del campus web) ---------------------------
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST")          # admite "host" o "host:puerto"
DB_NAME = os.getenv("DB_NAME")
DB_POOL_SIZE = _entero("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _entero("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _entero("DB_POOL_TIMEOUT", 30)

# --- JWT ---------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = (os.getenv("ALGORITHM") or "HS256").strip()
JWT_EXPIRE_MINUTES = _entero("ACCESS_TOKEN_EXPIRE_MINUTES", 60)

# --- Entorno -----------------------------------------------------------------
ES_PRODUCCION = (os.getenv("ENTORNO") or "desarrollo").strip().lower() in (
    "produccion", "producción", "production", "prod")
ALLOWED_ORIGINS = [o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or "").split(",") if o.strip()]
MAX_CONTENT_MB = _entero("MAX_CONTENT_MB", 12)   # tope de tamaño de una petición
BCRYPT_ROUNDS = max(10, min(_entero("BCRYPT_ROUNDS", 12), 16))


def verificar() -> None:
    """Falla al arrancar, con un mensaje claro, si falta algo esencial."""
    faltan = [n for n, v in (("DB_USER", DB_USER), ("DB_HOST", DB_HOST),
                             ("DB_NAME", DB_NAME), ("SECRET_KEY", SECRET_KEY)) if not v]
    if faltan:
        raise RuntimeError("Faltan variables de entorno: " + ", ".join(faltan))
    if len(SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY es demasiado corta: usa al menos 32 caracteres aleatorios.")
