"""Reglas de las clases virtuales: el docente publica el enlace de una clase en
línea (Meet, Zoom...) y los alumnos del curso la consultan."""
from app.database import get_db
from app.errors import ApiError
from app.repositories import clase_repository
from app.services import cursos_service
from app.utils import enlace, fecha_hora, texto


def _validar(datos: dict) -> dict:
    """fecha (AAAA-MM-DDTHH:MM) y enlace son obligatorios; tema es opcional."""
    return {
        "tema": texto(datos, "tema", minimo=0, maximo=150, requerido=False) or None,
        "fecha": fecha_hora(datos, "fecha"),
        "enlace": enlace(datos, "enlace", requerido=True),
    }


def _buscar(id_clase: int) -> dict:
    clase = clase_repository.buscar(id_clase)
    if clase is None:
        raise ApiError(404, "Clase no encontrada")
    return clase


def listar(usuario: dict, id_carga: int) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_ver_curso(usuario, carga)
    return {"curso": carga, "clases": clase_repository.listar(id_carga)}


def crear(usuario: dict, id_carga: int, datos: dict) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_docente_del_curso(usuario, carga)
    c = _validar(datos)

    db = get_db()
    try:
        id_clase = clase_repository.crear(id_carga, c["tema"], c["fecha"], c["enlace"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Clase publicada", "clase": clase_repository.buscar(id_clase)}


def editar(usuario: dict, id_clase: int, datos: dict) -> dict:
    clase = _buscar(id_clase)
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(clase["id_carga_academica"]))
    c = _validar(datos)

    db = get_db()
    try:
        clase_repository.actualizar(id_clase, c["tema"], c["fecha"], c["enlace"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Clase actualizada", "clase": clase_repository.buscar(id_clase)}


def eliminar(usuario: dict, id_clase: int) -> dict:
    clase = _buscar(id_clase)
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(clase["id_carga_academica"]))

    db = get_db()
    try:
        clase_repository.eliminar(id_clase)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Clase eliminada"}
