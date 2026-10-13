"""Módulo Material de clase: el docente publica material y los alumnos lo consultan.

GET    /material/<id_carga>?bimestre=<n>   ver el material de un curso (filtro opcional)
POST   /material/<id_carga>                el docente publica un material nuevo
PUT    /material/item/<id_material>        el docente edita un material
DELETE /material/item/<id_material>        el docente borra un material

Cuerpo JSON para POST y PUT:
    {"titulo": "...", "bimestre": 1, "descripcion": "...", "archivo_url": "https://..."}
    titulo y bimestre son obligatorios; descripcion y archivo_url son opcionales.
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required
from app.database import get_db
from app.errors import ApiError
from app.models.virtual import MaterialClase
from app.services import cursos
from app.utils import a_dict, entero, json_requerido, texto

bp = Blueprint("material", __name__, url_prefix="/material")


# --- Funciones de ayuda ------------------------------------------------------

def _leer_material(datos: dict) -> dict:
    """Valida el JSON de un material y devuelve los campos listos para guardar."""
    archivo_url = texto(datos, "archivo_url", minimo=0, maximo=255, requerido=False) or None
    # El material se comparte como enlace (Drive, YouTube, PDF en la web...).
    if archivo_url and not archivo_url.startswith(("http://", "https://")):
        raise ApiError(400, "El enlace debe empezar con http:// o https://")
    return {
        "titulo": texto(datos, "titulo", minimo=3, maximo=150),
        "bimestre": entero(datos, "bimestre", minimo=1, maximo=4),
        "descripcion": texto(datos, "descripcion", minimo=0, maximo=2000, requerido=False) or None,
        "archivo_url": archivo_url,
    }


def _buscar_material(db, id_material: int) -> MaterialClase:
    """Material por su id, o error 404."""
    material = db.get(MaterialClase, id_material)
    if material is None:
        raise ApiError(404, "Material no encontrado")
    return material


# --- Rutas -------------------------------------------------------------------

@bp.get("/<int:id_carga>")
@jwt_required()
def listar_material(id_carga):
    db = get_db()
    carga = cursos.buscar_carga(db, id_carga)
    # Pueden verlo el docente del curso, sus alumnos y el ADMIN.
    cursos.exigir_ver_curso(db, carga)

    consulta = db.query(MaterialClase).filter(MaterialClase.id_carga_academica == id_carga)

    # Filtro opcional: /material/5?bimestre=2
    bimestre = request.args.get("bimestre", type=int)
    if bimestre is not None:
        consulta = consulta.filter(MaterialClase.bimestre == bimestre)

    # Los más recientes primero.
    materiales = consulta.order_by(MaterialClase.fecha_publicacion.desc(),
                                   MaterialClase.id_material.desc()).all()
    return jsonify({
        "curso": cursos.curso_a_dict(carga),
        "materiales": [a_dict(m) for m in materiales],
    })


@bp.post("/<int:id_carga>")
@jwt_required("DOCENTE")
def publicar_material(id_carga):
    db = get_db()
    carga = cursos.buscar_carga(db, id_carga)
    cursos.exigir_docente_del_curso(db, carga)   # solo el docente que dicta el curso

    material = MaterialClase(id_carga_academica=id_carga, **_leer_material(json_requerido()))
    db.add(material)
    db.commit()
    db.refresh(material)   # recarga la fila para obtener el id y la fecha que puso MySQL

    return jsonify({"message": "Material publicado", "material": a_dict(material)}), 201


@bp.put("/item/<int:id_material>")
@jwt_required("DOCENTE")
def editar_material(id_material):
    db = get_db()
    material = _buscar_material(db, id_material)
    cursos.exigir_docente_del_curso(db, cursos.buscar_carga(db, material.id_carga_academica))

    # PUT reemplaza el material completo: los campos opcionales que no se
    # envíen quedan vacíos.
    for campo, valor in _leer_material(json_requerido()).items():
        setattr(material, campo, valor)
    db.commit()

    return jsonify({"message": "Material actualizado", "material": a_dict(material)})


@bp.delete("/item/<int:id_material>")
@jwt_required("DOCENTE")
def borrar_material(id_material):
    db = get_db()
    material = _buscar_material(db, id_material)
    cursos.exigir_docente_del_curso(db, cursos.buscar_carga(db, material.id_carga_academica))

    db.delete(material)
    db.commit()
    return jsonify({"message": "Material eliminado"})
