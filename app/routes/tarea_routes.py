"""Módulo Tareas y entregas.

GET    /tareas/<id_carga>                          ver las tareas (docente, alumnos del curso o ADMIN)
POST   /tareas/<id_carga>                          DOCENTE del curso: publica una tarea
DELETE /tareas/item/<id_tarea>                     DOCENTE del curso: borra (409 si ya tiene entregas)
POST   /tareas/item/<id_tarea>/entregar            ALUMNO del curso: entrega con un enlace
GET    /tareas/item/<id_tarea>/entregas            DOCENTE del curso: quién entregó y quién no
PATCH  /tareas/entregas/<id_entrega>/calificar     DOCENTE del curso: nota 0-20 y observación

JSON:
    publicar:  {"titulo", "fecha_entrega": "2026-11-20T23:59", "bimestre", "descripcion"?, "archivo_url"?}
    entregar:  {"archivo_url": "https://...", "comentario"?}
    calificar: {"calificacion": 17, "observacion"?}
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import tarea_service
from app.utils import json_requerido

bp = Blueprint("tareas", __name__, url_prefix="/tareas")


@bp.get("/<int:id_carga>")
@jwt_required()
def listar(id_carga):
    return jsonify(tarea_service.listar(usuario_actual(), id_carga))


@bp.post("/<int:id_carga>")
@jwt_required("DOCENTE")
def publicar(id_carga):
    return jsonify(tarea_service.publicar(usuario_actual(), id_carga, json_requerido())), 201


@bp.delete("/item/<int:id_tarea>")
@jwt_required("DOCENTE")
def eliminar(id_tarea):
    return jsonify(tarea_service.eliminar(usuario_actual(), id_tarea))


@bp.post("/item/<int:id_tarea>/entregar")
@jwt_required("ALUMNO")
def entregar(id_tarea):
    respuesta, codigo = tarea_service.entregar(usuario_actual(), id_tarea, json_requerido())
    return jsonify(respuesta), codigo


@bp.get("/item/<int:id_tarea>/entregas")
@jwt_required("DOCENTE")
def entregas(id_tarea):
    return jsonify(tarea_service.entregas(usuario_actual(), id_tarea))


@bp.patch("/entregas/<int:id_entrega>/calificar")
@jwt_required("DOCENTE")
def calificar(id_entrega):
    return jsonify(tarea_service.calificar(usuario_actual(), id_entrega, json_requerido()))
