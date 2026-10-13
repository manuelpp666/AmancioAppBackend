"""Preparar la base de datos de la app: crear las tablas y cargar datos de prueba.

Se usa desde la consola:
    flask --app run crear-tablas     crea las tablas que faltan (no borra nada)
    flask --app run datos-prueba     agrega los datos de prueba (si aún no existen)

Usuarios de prueba (contraseña inicial = su DNI, como en el colegio):
    ADM-11111111  administrador
    DOC-22222222  docente Carlos   → dicta Matemática
    DOC-66666666  docente María    → dicta Comunicación y Ciencia y Tecnología
    ALU-33333333  alumna Lucía     → 3ro "A" de Secundaria  ┐ hermanos: comparten
    ALU-44444444  alumno Mateo     → 1ro "A" de Secundaria  ┘ el mismo familiar

Datos académicos: año 2026 (activo) con 4 bimestres, Primaria y Secundaria con
sus grados, secciones 1ro A, 3ro A y 3ro B de Secundaria, 3 cursos dictados en
1ro A y 3ro A, y dos materiales de ejemplo en Matemática de 3ro A.
"""
from datetime import date

from app import database
from app.database import Base
from app.models.academico import AnioEscolar, Area, Bimestre, Curso, Grado, Nivel, Seccion
from app.models.alumno import Alumno
from app.models.docente import Docente
from app.models.familiar import Familiar
from app.models.gestion import CargaAcademica
from app.models.matricula import Matricula
from app.models.personal import Administrador
from app.models.usuario import Usuario
from app.models.virtual import MaterialClase
from app.security import get_password_hash

ANIO = "2026"


def crear_tablas() -> list[str]:
    """Crea en MySQL todas las tablas definidas en los modelos. Devuelve sus nombres."""
    import app.models  # noqa: F401  (carga todos los modelos)
    # create_all solo crea las tablas que no existen; las que ya están no se tocan.
    Base.metadata.create_all(bind=database.engine)
    return sorted(Base.metadata.tables)


def cargar_datos_prueba() -> list[str]:
    """Agrega los datos de prueba que falten. Devuelve qué se creó."""
    db = database.SessionLocal()
    try:
        creados = _cargar_usuarios(db)
        if _cargar_academico(db):
            creados.append(f"datos académicos del año {ANIO}")
        db.commit()   # guarda todo junto
        return creados
    finally:
        db.close()


# --- Usuarios ----------------------------------------------------------------

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


def _cargar_usuarios(db) -> list[str]:
    creados = []

    # --- Administrador ---
    if not _existe(db, "ADM-11111111"):
        user = _crear_usuario(db, "ADM-11111111", "ADMIN")
        db.add(Administrador(id_usuario=user.id_usuario, dni="11111111",
                             nombres="Ana", apellidos="Torres Ruiz",
                             email="admin@example.com", telefono="911111111",
                             permisos=["*"]))
        creados.append(user.username)

    # --- Docentes ---
    docentes = [
        ("DOC-22222222", "Carlos", "Mendoza Paz", "Matemática", "carlos@example.com", "922222222"),
        ("DOC-66666666", "María", "Salazar Vega", "Comunicación", "maria@example.com", "966666666"),
    ]
    for username, nombres, apellidos, especialidad, email, telefono in docentes:
        if _existe(db, username):
            continue
        user = _crear_usuario(db, username, "DOCENTE")
        db.add(Docente(id_usuario=user.id_usuario, dni=username.split("-")[1],
                       nombres=nombres, apellidos=apellidos, especialidad=especialidad,
                       email=email, telefono=telefono))
        creados.append(username)

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

    db.flush()
    return creados


# --- Datos académicos --------------------------------------------------------

def _ficha_docente(db, username: str) -> Docente:
    user = db.query(Usuario).filter(Usuario.username == username).one()
    return db.query(Docente).filter(Docente.id_usuario == user.id_usuario).one()


def _ficha_alumno(db, username: str) -> Alumno:
    user = db.query(Usuario).filter(Usuario.username == username).one()
    return db.query(Alumno).filter(Alumno.id_usuario == user.id_usuario).one()


def _cargar_academico(db) -> bool:
    """Crea el año escolar y todo lo que depende de él. False si ya existía."""
    if db.get(AnioEscolar, ANIO) is not None:
        return False

    # 1. Año escolar activo y sus 4 bimestres.
    db.add(AnioEscolar(id_anio_escolar=ANIO, fecha_inicio=date(2026, 3, 9),
                       fecha_fin=date(2026, 12, 18), activo=True, tipo="REGULAR"))
    fechas_bimestres = [
        (date(2026, 3, 9), date(2026, 5, 8)),
        (date(2026, 5, 18), date(2026, 7, 24)),
        (date(2026, 8, 10), date(2026, 10, 9)),
        (date(2026, 10, 19), date(2026, 12, 18)),
    ]
    for numero, (inicio, fin) in enumerate(fechas_bimestres, start=1):
        db.add(Bimestre(id_anio_escolar=ANIO, numero=numero, fecha_inicio=inicio, fecha_fin=fin))

    # 2. Niveles y grados (orden 1 a 11: primero Primaria, luego Secundaria).
    primaria, secundaria = Nivel(nombre="Primaria"), Nivel(nombre="Secundaria")
    db.add_all([primaria, secundaria])
    nombres = ["1ro", "2do", "3ro", "4to", "5to", "6to"]
    grados_sec = {}
    for i, nombre in enumerate(nombres, start=1):
        db.add(Grado(nivel=primaria, nombre=nombre, orden=i))
    for i, nombre in enumerate(nombres[:5], start=7):
        grados_sec[nombre] = Grado(nivel=secundaria, nombre=nombre, orden=i)
        db.add(grados_sec[nombre])

    # 3. Secciones del 2026.
    sec_1a = Seccion(grado=grados_sec["1ro"], id_anio_escolar=ANIO, nombre="A")
    sec_3a = Seccion(grado=grados_sec["3ro"], id_anio_escolar=ANIO, nombre="A")
    sec_3b = Seccion(grado=grados_sec["3ro"], id_anio_escolar=ANIO, nombre="B")
    db.add_all([sec_1a, sec_3a, sec_3b])

    # 4. Áreas y cursos (aquí cada área tiene un curso con el mismo nombre).
    cursos = {}
    for nombre in ["Matemática", "Comunicación", "Ciencia y Tecnología"]:
        cursos[nombre] = Curso(area=Area(nombre=nombre), nombre=nombre, minutos_semanales=270)
        db.add(cursos[nombre])

    # 5. Carga académica: qué docente dicta cada curso en cada sección.
    carlos = _ficha_docente(db, "DOC-22222222")
    maria = _ficha_docente(db, "DOC-66666666")
    db.flush()   # para tener los ids de secciones y cursos
    quien_dicta = {"Matemática": carlos, "Comunicación": maria, "Ciencia y Tecnología": maria}
    mate_3a = None
    for seccion in (sec_1a, sec_3a):
        for nombre_curso, docente in quien_dicta.items():
            carga = CargaAcademica(id_anio_escolar=ANIO, id_seccion=seccion.id_seccion,
                                   id_curso=cursos[nombre_curso].id_curso,
                                   id_docente=docente.id_docente)
            db.add(carga)
            if seccion is sec_3a and nombre_curso == "Matemática":
                mate_3a = carga

    # 6. Matrículas: Lucía en 3ro A y Mateo en 1ro A.
    for username, seccion in (("ALU-33333333", sec_3a), ("ALU-44444444", sec_1a)):
        db.add(Matricula(id_anio_escolar=ANIO, id_alumno=_ficha_alumno(db, username).id_alumno,
                         id_grado=seccion.id_grado, id_seccion=seccion.id_seccion))

    # 7. Material de ejemplo en Matemática de 3ro A.
    db.flush()
    db.add_all([
        MaterialClase(id_carga_academica=mate_3a.id_carga_academica, bimestre=1,
                      titulo="Ecuaciones de primer grado",
                      descripcion="Teoría y 10 ejercicios resueltos.",
                      archivo_url="https://example.com/ecuaciones.pdf"),
        MaterialClase(id_carga_academica=mate_3a.id_carga_academica, bimestre=2,
                      titulo="Sistemas de ecuaciones",
                      descripcion="Video explicativo del método de sustitución.",
                      archivo_url="https://example.com/sistemas"),
    ])
    return True
