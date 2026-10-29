"""Módulo Notas y libreta.

GET  /notas/<id_carga>?bimestre=<n>        DOCENTE del curso (o ADMIN): registro de notas del curso
POST /notas/<id_carga>                     DOCENTE del curso: registra las notas de una evaluación
POST /notas/<id_carga>/cerrar-bimestre     DOCENTE del curso: cierra el bimestre (pasa a la libreta)
GET  /notas/mis-notas?bimestre=<n>         ALUMNO: sus cursos con evaluaciones y promedio
GET  /notas/mi-libreta                     ALUMNO: promedios de los bimestres cerrados

Si no se indica ?bimestre, se usa el bimestre en curso.

JSON de POST /notas/<id_carga>:
    {"bimestre": 3, "evaluacion": "Práctica 1",
     "notas": [{"id_alumno": 1, "valor": 15.5}, {"id_alumno": 3, "valor": 18}]}
JSON de /cerrar-bimestre:  {"bimestre": 3}
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.offline import idempotente
from app.services import nota_service
from app.utils import json_requerido

bp = Blueprint("notas", __name__, url_prefix="/notas")


@bp.get("/<int:id_carga>")
@jwt_required("DOCENTE", "ADMIN")
def notas_del_curso(id_carga):
    bimestre = request.args.get("bimestre", type=int)
    return jsonify(nota_service.notas_del_curso(usuario_actual(), id_carga, bimestre))


@bp.post("/<int:id_carga>")
@jwt_required("DOCENTE")
@idempotente
def registrar_notas(id_carga):
    return jsonify(nota_service.registrar_notas(usuario_actual(), id_carga, json_requerido())), 201


@bp.post("/<int:id_carga>/cerrar-bimestre")
@jwt_required("DOCENTE")
def cerrar_bimestre(id_carga):
    return jsonify(nota_service.cerrar_bimestre(usuario_actual(), id_carga, json_requerido()))


@bp.get("/mis-notas")
@jwt_required("ALUMNO")
def mis_notas():
    bimestre = request.args.get("bimestre", type=int)
    return jsonify(nota_service.mis_notas(usuario_actual(), bimestre))


@bp.get("/mi-libreta")
@jwt_required("ALUMNO")
def mi_libreta():
    return jsonify(nota_service.mi_libreta(usuario_actual()))
