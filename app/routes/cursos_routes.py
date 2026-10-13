"""Módulo Mis cursos.

GET /cursos/mis-cursos              alumno: cursos de su sección · docente: cursos que dicta
GET /cursos/<id_carga>/alumnos      docente del curso (o ADMIN): alumnos matriculados
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import cursos_service

bp = Blueprint("cursos", __name__, url_prefix="/cursos")


@bp.get("/mis-cursos")
@jwt_required("ALUMNO", "DOCENTE")
def mis_cursos():
    return jsonify(cursos_service.mis_cursos(usuario_actual()))


@bp.get("/<int:id_carga>/alumnos")
@jwt_required("DOCENTE", "ADMIN")
def alumnos_del_curso(id_carga):
    return jsonify(cursos_service.alumnos_del_curso(usuario_actual(), id_carga))
