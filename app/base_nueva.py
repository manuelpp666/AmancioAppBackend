"""Preparar la base de datos de la app: crear las tablas y cargar datos de prueba.

Se usa desde la consola:
    flask --app run crear-tablas     crea las tablas que faltan (no borra nada)
    flask --app run datos-prueba     agrega los usuarios de prueba (si aún no existen)

Usuarios de prueba (contraseña inicial = su DNI, como en el colegio):
    ADM-11111111  administrador
    DOC-22222222  docente
    ALU-33333333  alumna  ┐ hermanos: comparten el mismo familiar
    ALU-44444444  alumno  ┘
"""
from app import database
from app.database import Base
from app.models.alumno import Alumno
from app.models.docente import Docente
from app.models.familiar import Familiar
from app.models.personal import Administrador
from app.models.usuario import Usuario
from app.security import get_password_hash


def crear_tablas() -> list[str]:
    """Crea en MySQL todas las tablas definidas en los modelos. Devuelve sus nombres."""
    import app.models  # noqa: F401  (carga todos los modelos)
    # create_all solo crea las tablas que no existen; las que ya están no se tocan.
    Base.metadata.create_all(bind=database.engine)
    return sorted(Base.metadata.tables)


def _existe(db, username: str) -> bool:
    return db.query(Usuario).filter(Usuario.username == username).first() is not None


def _crear_usuario(db, username: str, rol: str) -> Usuario:
    """Crea la cuenta. La contraseña inicial es el DNI (lo que va después del guion)."""
    dni = username.split("-")[1]
    user = Usuario(username=username, rol=rol, activo=True, debe_cambiar_password=False,
                   password_hash=get_password_hash(dni))
    db.add(user)
    db.flush()   # envía el INSERT ya, para conocer el id_usuario que asignó MySQL
    return user


def cargar_datos_prueba() -> list[str]:
    """Agrega los usuarios de prueba que falten. Devuelve los usernames creados."""
    db = database.SessionLocal()
    creados = []
    try:
        # --- Administrador ---
        if not _existe(db, "ADM-11111111"):
            user = _crear_usuario(db, "ADM-11111111", "ADMIN")
            db.add(Administrador(id_usuario=user.id_usuario, dni="11111111",
                                 nombres="Ana", apellidos="Torres Ruiz",
                                 email="admin@example.com", telefono="911111111",
                                 permisos=["*"]))
            creados.append(user.username)

        # --- Docente ---
        if not _existe(db, "DOC-22222222"):
            user = _crear_usuario(db, "DOC-22222222", "DOCENTE")
            db.add(Docente(id_usuario=user.id_usuario, dni="22222222",
                           nombres="Carlos", apellidos="Mendoza Paz",
                           especialidad="Matemática", email="carlos@example.com",
                           telefono="922222222"))
            creados.append(user.username)

        # --- Familiar (la mamá de los dos alumnos) ---
        familiar = db.query(Familiar).filter(Familiar.dni == "55555555").first()
        if familiar is None:
            familiar = Familiar(dni="55555555", nombres="Rosa", apellidos="Quispe Flores",
                                telefono="955555555", email="rosa.quispe@example.com",
                                direccion="Av. Los Próceres 123, Lima")
            db.add(familiar)

        # --- Dos alumnos hermanos, con el mismo familiar ---
        hermanos = [("ALU-33333333", "Lucía", "F"), ("ALU-44444444", "Mateo", "M")]
        for username, nombre, genero in hermanos:
            if _existe(db, username):
                continue
            user = _crear_usuario(db, username, "ALUMNO")
            db.add(Alumno(id_usuario=user.id_usuario, dni=username.split("-")[1],
                          nombres=nombre, apellidos="Quispe Flores", genero=genero,
                          direccion="Av. Los Próceres 123, Lima",
                          estado_ingreso="ESTUDIANTE", familiar=familiar))
            creados.append(username)

        db.commit()   # guarda todo junto
        return creados
    finally:
        db.close()
