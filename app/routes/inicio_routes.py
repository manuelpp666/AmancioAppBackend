"""Módulo Panel de inicio.

GET /inicio    resumen del día según el rol del token (alumno, docente, auxiliar,
               psicólogo o administrador). Ver app/services/inicio_service.py.
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import inicio_service

bp = Blueprint("inicio", __name__, url_prefix="/inicio")


@bp.get("")
@jwt_required()
def panel():
    return jsonify(inicio_service.panel(usuario_actual()))
