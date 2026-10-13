"""Módulo Asistencia.

POST /asistencia/lote                               AUXILIAR: registra toda una sección (transacción)
GET  /asistencia/seccion/<id_seccion>?fecha=<f>     AUXILIAR, DOCENTE, ADMIN: asistencia de un día
GET  /asistencia/mia                                ALUMNO: su historial y resumen

JSON de /lote:
    {"id_seccion": 2, "fecha": "2026-10-13",
     "registros": [{"id_alumno": 1, "estado": "P"},
                   {"id_alumno": 3, "estado": "T", "observacion": "Llegó 8:15"}]}
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import asistencia_service
from app.utils import fecha_de_query, json_requerido

bp = Blueprint("asistencia", __name__, url_prefix="/asistencia")


@bp.post("/lote")
@jwt_required("AUXILIAR")
def registrar_lote():
    return jsonify(asistencia_service.registrar_lote(json_requerido())), 201


@bp.get("/seccion/<int:id_seccion>")
@jwt_required("AUXILIAR", "DOCENTE", "ADMIN")
def de_seccion(id_seccion):
    return jsonify(asistencia_service.de_seccion(id_seccion, fecha_de_query()))


@bp.get("/mia")
@jwt_required("ALUMNO")
def mi_asistencia():
    return jsonify(asistencia_service.mi_asistencia(usuario_actual()))
