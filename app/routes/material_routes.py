"""Módulo Material de clase.

GET    /material/<id_carga>?bimestre=<n>   ver (docente del curso, sus alumnos o ADMIN)
POST   /material/<id_carga>                publicar (docente del curso)
PUT    /material/item/<id_material>        editar (docente del curso)
DELETE /material/item/<id_material>        borrar (docente del curso)

JSON de POST y PUT: {"titulo", "bimestre" (1-4), "descripcion"?, "archivo_url"?}
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.services import material_service
from app.utils import json_requerido

bp = Blueprint("material", __name__, url_prefix="/material")


@bp.get("/<int:id_carga>")
@jwt_required()
def listar(id_carga):
    bimestre = request.args.get("bimestre", type=int)   # ?bimestre=2 (opcional)
    return jsonify(material_service.listar(usuario_actual(), id_carga, bimestre))


@bp.post("/<int:id_carga>")
@jwt_required("DOCENTE")
def publicar(id_carga):
    return jsonify(material_service.publicar(usuario_actual(), id_carga, json_requerido())), 201


@bp.put("/item/<int:id_material>")
@jwt_required("DOCENTE")
def editar(id_material):
    return jsonify(material_service.editar(usuario_actual(), id_material, json_requerido()))


@bp.delete("/item/<int:id_material>")
@jwt_required("DOCENTE")
def eliminar(id_material):
    return jsonify(material_service.eliminar(usuario_actual(), id_material))
