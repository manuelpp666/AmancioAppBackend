"""Módulo Citas de psicología.

POST  /citas                           ALUMNO: solicita una cita
GET   /citas/mis-citas                 ALUMNO: su historial
GET   /citas/agenda?fecha=<f>          PSICOLOGO: citas del día y solicitudes pendientes
PATCH /citas/<id_cita>/programar       PSICOLOGO: {"fecha_cita": "2026-10-20T10:00"}
PATCH /citas/<id_cita>/completar       PSICOLOGO: {"observacion": "..."}
PATCH /citas/<id_cita>/cancelar        PSICOLOGO: {"motivo": "..."}
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import cita_service
from app.utils import fecha_de_query, json_requerido

bp = Blueprint("citas", __name__, url_prefix="/citas")


@bp.post("")
@jwt_required("ALUMNO")
def solicitar():
    return jsonify(cita_service.solicitar(usuario_actual(), json_requerido())), 201


@bp.get("/mis-citas")
@jwt_required("ALUMNO")
def mis_citas():
    return jsonify(cita_service.mis_citas(usuario_actual()))


@bp.get("/agenda")
@jwt_required("PSICOLOGO")
def agenda():
    return jsonify(cita_service.agenda(fecha_de_query()))


@bp.patch("/<int:id_cita>/programar")
@jwt_required("PSICOLOGO")
def programar(id_cita):
    return jsonify(cita_service.programar(usuario_actual(), id_cita, json_requerido()))


@bp.patch("/<int:id_cita>/completar")
@jwt_required("PSICOLOGO")
def completar(id_cita):
    return jsonify(cita_service.completar(id_cita, json_requerido()))


@bp.patch("/<int:id_cita>/cancelar")
@jwt_required("PSICOLOGO")
def cancelar(id_cita):
    return jsonify(cita_service.cancelar(id_cita, json_requerido()))
