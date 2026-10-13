"""Módulo Clases virtuales: enlaces de clases en línea de cada curso.

GET    /clases/<id_carga>           ver (docente del curso, sus alumnos o ADMIN)
POST   /clases/<id_carga>           publicar (docente del curso)
PUT    /clases/item/<id_clase>      editar (docente del curso)
DELETE /clases/item/<id_clase>      borrar (docente del curso)

JSON de POST y PUT: {"fecha": "2026-10-20T10:00", "enlace": "https://...", "tema"?}
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import clase_service
from app.utils import json_requerido

bp = Blueprint("clases", __name__, url_prefix="/clases")


@bp.get("/<int:id_carga>")
@jwt_required()
def listar(id_carga):
    return jsonify(clase_service.listar(usuario_actual(), id_carga))


@bp.post("/<int:id_carga>")
@jwt_required("DOCENTE")
def crear(id_carga):
    return jsonify(clase_service.crear(usuario_actual(), id_carga, json_requerido())), 201


@bp.put("/item/<int:id_clase>")
@jwt_required("DOCENTE")
def editar(id_clase):
    return jsonify(clase_service.editar(usuario_actual(), id_clase, json_requerido()))


@bp.delete("/item/<int:id_clase>")
@jwt_required("DOCENTE")
def eliminar(id_clase):
    return jsonify(clase_service.eliminar(usuario_actual(), id_clase))
