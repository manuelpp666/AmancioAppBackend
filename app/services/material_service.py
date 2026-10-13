"""Reglas del material de clase: el docente publica, los alumnos consultan."""
from app.database import get_db
from app.errors import ApiError
from app.repositories import material_repository
from app.services import cursos_service
from app.utils import enlace, entero, texto


def _validar(datos: dict) -> dict:
    """Valida el JSON de un material. titulo y bimestre son obligatorios."""
    return {
        "titulo": texto(datos, "titulo", minimo=3, maximo=150),
        "bimestre": entero(datos, "bimestre", minimo=1, maximo=4),
        "descripcion": texto(datos, "descripcion", minimo=0, maximo=2000, requerido=False) or None,
        "archivo_url": enlace(datos, "archivo_url", maximo=255),
    }


def _buscar(id_material: int) -> dict:
    material = material_repository.buscar(id_material)
    if material is None:
        raise ApiError(404, "Material no encontrado")
    return material


def listar(usuario: dict, id_carga: int, bimestre=None) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_ver_curso(usuario, carga)
    return {"curso": carga, "materiales": material_repository.listar(id_carga, bimestre)}


def publicar(usuario: dict, id_carga: int, datos: dict) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_docente_del_curso(usuario, carga)
    m = _validar(datos)

    db = get_db()
    try:
        id_material = material_repository.crear(id_carga, m["titulo"], m["bimestre"],
                                                 m["descripcion"], m["archivo_url"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Material publicado", "material": material_repository.buscar(id_material)}


def editar(usuario: dict, id_material: int, datos: dict) -> dict:
    """PUT reemplaza el material completo: los campos opcionales que no se envíen quedan vacíos."""
    material = _buscar(id_material)
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(material["id_carga_academica"]))
    m = _validar(datos)

    db = get_db()
    try:
        material_repository.actualizar(id_material, m["titulo"], m["bimestre"],
                                       m["descripcion"], m["archivo_url"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Material actualizado", "material": material_repository.buscar(id_material)}


def eliminar(usuario: dict, id_material: int) -> dict:
    material = _buscar(id_material)
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(material["id_carga_academica"]))

    db = get_db()
    try:
        material_repository.eliminar(id_material)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Material eliminado"}
