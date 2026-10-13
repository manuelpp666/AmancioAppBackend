"""Lógica compartida por los módulos "Mis cursos" y "Material de clase".

Idea clave: un "curso" en la app es una **carga académica**, es decir,
un curso dictado por un docente en una sección durante un año.
    Ej.: Matemática · 3ro "A" de Secundaria · 2026 · docente Carlos

¿Quién puede ver un curso?
    - el docente que lo dicta
    - los alumnos matriculados en esa sección ese año
    - un ADMIN
¿Quién puede publicar material en un curso?  Solo el docente que lo dicta.
"""
from app.auth import usuario_actual
from app.errors import ApiError
from app.models.academico import AnioEscolar
from app.models.alumno import Alumno
from app.models.docente import Docente
from app.models.gestion import CargaAcademica
from app.models.matricula import Matricula


# --- Consultas básicas -------------------------------------------------------

def anio_activo(db) -> AnioEscolar:
    """Año escolar en curso (el marcado como activo), o error 404 si no hay ninguno."""
    anio = db.query(AnioEscolar).filter(AnioEscolar.activo.is_(True)).first()
    if anio is None:
        raise ApiError(404, "No hay un año escolar activo")
    return anio


def docente_de(db, id_usuario: int):
    """Ficha de docente de una cuenta, o None."""
    return db.query(Docente).filter(Docente.id_usuario == id_usuario).first()


def alumno_de(db, id_usuario: int):
    """Ficha de alumno de una cuenta, o None."""
    return db.query(Alumno).filter(Alumno.id_usuario == id_usuario).first()


def matricula_del_anio(db, id_alumno: int, id_anio: str):
    """Matrícula del alumno en ese año, o None si no está matriculado."""
    return (db.query(Matricula)
            .filter(Matricula.id_alumno == id_alumno, Matricula.id_anio_escolar == id_anio)
            .first())


def buscar_carga(db, id_carga: int) -> CargaAcademica:
    """Curso (carga académica) por su id, o error 404."""
    carga = db.get(CargaAcademica, id_carga)
    if carga is None:
        raise ApiError(404, "Curso no encontrado")
    return carga


# --- Permisos ----------------------------------------------------------------

def _es_el_docente(db, carga) -> bool:
    """True si quien hizo la petición es el docente que dicta este curso."""
    docente = docente_de(db, usuario_actual()["id"])
    return docente is not None and carga.id_docente == docente.id_docente


def _es_alumno_del_curso(db, carga) -> bool:
    """True si quien hizo la petición está matriculado en la sección de este curso."""
    alumno = alumno_de(db, usuario_actual()["id"])
    if alumno is None:
        return False
    matricula = matricula_del_anio(db, alumno.id_alumno, carga.id_anio_escolar)
    return matricula is not None and matricula.id_seccion == carga.id_seccion


def exigir_ver_curso(db, carga) -> None:
    """Error 403 si el usuario no puede ver este curso."""
    rol = usuario_actual()["rol"]
    if rol == "ADMIN":
        return
    if rol == "DOCENTE" and _es_el_docente(db, carga):
        return
    if rol == "ALUMNO" and _es_alumno_del_curso(db, carga):
        return
    raise ApiError(403, "No tienes acceso a este curso")


def exigir_docente_del_curso(db, carga) -> None:
    """Error 403 si el usuario no es el docente que dicta este curso."""
    if not _es_el_docente(db, carga):
        raise ApiError(403, "Solo el docente de este curso puede hacer esto")


# --- Convertir a JSON --------------------------------------------------------

def curso_a_dict(carga) -> dict:
    """Datos de un curso (carga académica) para enviarlos a la app."""
    seccion = carga.seccion
    docente = carga.docente
    return {
        "id_carga_academica": carga.id_carga_academica,
        "id_curso": carga.id_curso,
        "curso": carga.curso.nombre,
        "area": carga.curso.area.nombre if carga.curso.area else None,
        "id_seccion": seccion.id_seccion,
        "seccion": seccion.nombre,
        "grado": seccion.grado.nombre,
        "nivel": seccion.grado.nivel.nombre,
        "anio": carga.id_anio_escolar,
        "docente": f"{docente.nombres} {docente.apellidos}" if docente else None,
    }
