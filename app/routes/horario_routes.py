"""Módulo Horario escolar.

GET /horario/mi-horario     ALUMNO: horario de su sección · DOCENTE: horario de sus cursos
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import horario_service

bp = Blueprint("horario", __name__, url_prefix="/horario")


@bp.get("/mi-horario")
@jwt_required("ALUMNO", "DOCENTE")
def mi_horario():
    return jsonify(horario_service.mi_horario(usuario_actual()))
