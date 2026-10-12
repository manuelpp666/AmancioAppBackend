"""Configuración del servidor.

Todo se lee de variables de entorno: en la PC vienen del archivo `.env`
(ver `.env.example`) y en Render se escriben en su panel. Así las contraseñas
nunca quedan escritas en el código.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # carga el archivo .env (si existe) en las variables de entorno


def _entero(nombre: str, defecto: int) -> int:
    """Lee una variable de entorno como número; si falta o no es número, usa el defecto."""
    try:
        return int(os.getenv(nombre) or defecto)
    except ValueError:
        return defecto


# --- Base de datos MySQL -----------------------------------------------------
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS", "")      # en XAMPP, root no tiene contraseña
DB_HOST = os.getenv("DB_HOST")          # "host" o "host:puerto", ej. 127.0.0.1:3310
DB_NAME = os.getenv("DB_NAME")

# --- JWT (token de sesión) ---------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")    # clave con la que se firman los tokens
JWT_ALGORITHM = os.getenv("ALGORITHM") or "HS256"
JWT_EXPIRE_MINUTES = _entero("ACCESS_TOKEN_EXPIRE_MINUTES", 60)  # duración del token

# --- Otros --------------------------------------------------------------------
# En producción se apaga el modo debug del servidor.
ES_PRODUCCION = (os.getenv("ENTORNO") or "desarrollo").strip().lower() == "produccion"
# Orígenes permitidos para CORS (solo si se prueba en navegador), separados por comas.
ALLOWED_ORIGINS = [o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or "").split(",") if o.strip()]
MAX_CONTENT_MB = _entero("MAX_CONTENT_MB", 12)   # tamaño máximo de una petición
# Costo del hash bcrypt: más alto = más seguro pero más lento. Se limita entre 10 y 16.
BCRYPT_ROUNDS = max(10, min(_entero("BCRYPT_ROUNDS", 12), 16))


def verificar() -> None:
    """Detiene el arranque con un mensaje claro si falta algo esencial en el .env."""
    obligatorias = {"DB_USER": DB_USER, "DB_HOST": DB_HOST, "DB_NAME": DB_NAME,
                    "SECRET_KEY": SECRET_KEY}
    faltan = [nombre for nombre, valor in obligatorias.items() if not valor]
    if faltan:
        raise RuntimeError("Faltan variables de entorno: " + ", ".join(faltan))
    if len(SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY es demasiado corta: usa al menos 32 caracteres aleatorios.")
