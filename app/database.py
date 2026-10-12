"""Conexión a MySQL con SQLAlchemy (el ORM: trabajar con tablas como clases de Python).

- `Base`: clase de la que heredan todos los modelos (cada modelo = una tabla).
- `init_db()`: abre la conexión al arrancar el servidor.
- `get_db()`: da la sesión de la petición actual, para consultar y guardar.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from app import config

# Base de todos los modelos. Se crea sin conectar, así los modelos se pueden
# importar aunque no haya base de datos (por ejemplo, en las pruebas).
Base = declarative_base()

# Fábrica de sesiones. `scoped_session` da una sesión distinta por cada petición
# (Flask atiende cada petición en su propio hilo), así no se mezclan los datos.
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))

# El "engine" es la conexión con MySQL. Se crea en init_db().
engine = None


def _url() -> URL:
    """Arma la dirección de conexión: mysql+pymysql://usuario:clave@host:puerto/base"""
    host, puerto = config.DB_HOST, None
    # Si DB_HOST viene como "127.0.0.1:3310", separar el host del puerto.
    if ":" in host:
        host, puerto = host.rsplit(":", 1)
        puerto = int(puerto)
    # URL.create escapa sola las contraseñas con caracteres especiales (@, /, #).
    return URL.create("mysql+pymysql", username=config.DB_USER, password=config.DB_PASS,
                      host=host, port=puerto, database=config.DB_NAME,
                      query={"charset": "utf8mb4"})   # utf8mb4 = tildes, ñ y emojis


def init_db() -> None:
    """Crea la conexión con MySQL. Se llama una vez, al arrancar el servidor."""
    global engine
    engine = create_engine(
        _url(),
        pool_size=5,         # conexiones abiertas que se reutilizan entre peticiones
        max_overflow=10,     # conexiones extra permitidas en momentos de mucha carga
        pool_pre_ping=True,  # comprueba que la conexión siga viva antes de usarla
        pool_recycle=1800,   # renueva cada conexión a los 30 min (MySQL cierra las viejas)
    )
    SessionLocal.configure(bind=engine)


def get_db():
    """Sesión de base de datos de la petición actual."""
    return SessionLocal()


def cerrar_sesion(_error=None) -> None:
    """Se ejecuta al final de cada petición: libera la sesión."""
    SessionLocal.remove()
