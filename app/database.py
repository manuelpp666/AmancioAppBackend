"""Conexión a MySQL con SQLAlchemy.

`Base` se define aquí, sin conectar, para que los modelos puedan importarse sin
variables de entorno. La conexión real se crea en `init_db()` al arrancar.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from app import config

Base = declarative_base()

# scoped_session: una sesión por petición/hilo (Flask atiende cada petición en
# su propio hilo). Se cierra en `cerrar_sesion`, registrado como teardown.
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))
engine = None


def _url() -> URL:
    host, puerto = config.DB_HOST, None
    if ":" in (host or ""):
        h, _, p = host.rpartition(":")
        if p.isdigit():
            host, puerto = h, int(p)
    # URL.create escapa bien las contraseñas con caracteres especiales (@, /, #).
    return URL.create("mysql+pymysql", username=config.DB_USER, password=config.DB_PASS,
                      host=host, port=puerto, database=config.DB_NAME,
                      query={"charset": "utf8mb4"})


def init_db() -> None:
    global engine
    engine = create_engine(
        _url(),
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout=config.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
    SessionLocal.configure(bind=engine)


def get_db():
    """Sesión de la petición actual."""
    return SessionLocal()


def cerrar_sesion(_exc=None) -> None:
    SessionLocal.remove()
