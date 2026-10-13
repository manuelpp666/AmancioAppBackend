"""Reglas de los cursos y de quién puede verlos o editarlos.

Un "curso" de la app es una carga académica: un curso dictado por un docente
en una sección durante un año (ej. Matemática · 3ro A · 2026 · Carlos).

¿Quién puede VER un curso?     su docente, los alumnos de esa sección y el ADMIN.
¿Quién puede EDITAR un curso?  (publicar material, clases...) solo su docente.

Estas reglas las usan también los services de material y de clases virtuales.
"""
from app.errors import ApiError
from app.repositories import cursos_repository, perfil_repository
from app.services import academico_service


def buscar_carga(id_carga: int) -> dict:
    carga = cursos_repository.buscar_carga(id_carga)
    if carga is None:
        raise ApiError(404, "Curso no encontrado")
    return carga


def matricula_actual(id_usuario: int):
    """Matrícula del alumno (por su cuenta) en el año activo, o None."""
    alumno = perfil_repository.alumno_por_usuario(id_usuario)
    if alumno is None:
        return None
    anio = academico_service.anio_activo()
    return cursos_repository.matricula_del_anio(alumno["id_alumno"], anio["id_anio_escolar"])


# --- Permisos -----------------------------------------------------------------

def _es_el_docente(usuario: dict, carga: dict) -> bool:
    docente = perfil_repository.docente_por_usuario(usuario["id"])
    return docente is not None and carga["id_docente"] == docente["id_docente"]


def _es_alumno_del_curso(usuario: dict, carga: dict) -> bool:
    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    if alumno is None:
        return False
    matricula = cursos_repository.matricula_del_anio(alumno["id_alumno"], carga["anio"])
    return matricula is not None and matricula["id_seccion"] == carga["id_seccion"]


def exigir_ver_curso(usuario: dict, carga: dict) -> None:
    """Error 403 si el usuario no puede ver este curso."""
    if usuario["rol"] == "ADMIN":
        return
    if usuario["rol"] == "DOCENTE" and _es_el_docente(usuario, carga):
        return
    if usuario["rol"] == "ALUMNO" and _es_alumno_del_curso(usuario, carga):
        return
    raise ApiError(403, "No tienes acceso a este curso")


def exigir_docente_del_curso(usuario: dict, carga: dict) -> None:
    """Error 403 si el usuario no es el docente que dicta este curso."""
    if not _es_el_docente(usuario, carga):
        raise ApiError(403, "Solo el docente de este curso puede hacer esto")


# --- Casos de uso ---------------------------------------------------------------

def mis_cursos(usuario: dict) -> list:
    """Alumno: cursos de su sección. Docente: cursos que dicta. Del año activo."""
    anio = academico_service.anio_activo()

    if usuario["rol"] == "ALUMNO":
        matricula = matricula_actual(usuario["id"])
        if matricula is None or matricula["id_seccion"] is None:
            return []   # todavía no está matriculado en una sección
        return cursos_repository.cursos_de_seccion(matricula["id_seccion"], anio["id_anio_escolar"])

    docente = perfil_repository.docente_por_usuario(usuario["id"])
    if docente is None:
        return []
    return cursos_repository.cursos_de_docente(docente["id_docente"], anio["id_anio_escolar"])


def alumnos_del_curso(usuario: dict, id_carga: int) -> dict:
    carga = buscar_carga(id_carga)
    # Un docente solo ve los alumnos de SUS cursos (el ADMIN, de todos).
    if usuario["rol"] == "DOCENTE":
        exigir_docente_del_curso(usuario, carga)
    alumnos = cursos_repository.alumnos_de_seccion(carga["id_seccion"], carga["anio"])
    return {"curso": carga, "alumnos": alumnos}
