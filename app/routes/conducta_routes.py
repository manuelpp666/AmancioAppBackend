"""Módulo Conducta.

GET   /conducta/faltas                          catálogo de faltas (cualquiera con sesión)
POST  /conducta/reportes                        AUXILIAR: registra un reporte
PATCH /conducta/reportes/<id_reporte>/anular    AUXILIAR o ADMIN: anula con motivo
GET   /conducta/alumno/<id_alumno>              nota de conducta y reportes (el propio alumno o el personal)

JSON de POST /reportes:
    {"id_alumno": 1, "id_falta": 3, "descripcion": "...", "fecha"?: "2026-10-13",
     "evidencia_url"?: "https://..."}
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import conducta_service
from app.utils import json_requerido

bp = Blueprint("conducta", __name__, url_prefix="/conducta")


@bp.get("/faltas")
@jwt_required()
def faltas():
    return jsonify(conducta_service.catalogo())


@bp.post("/reportes")
@jwt_required("AUXILIAR")
def registrar_reporte():
    return jsonify(conducta_service.registrar_reporte(usuario_actual(), json_requerido())), 201


@bp.patch("/reportes/<int:id_reporte>/anular")
@jwt_required("AUXILIAR", "ADMIN")
def anular_reporte(id_reporte):
    return jsonify(conducta_service.anular_reporte(usuario_actual(), id_reporte, json_requerido()))


@bp.get("/alumno/<int:id_alumno>")
@jwt_required()
def estado_conducta(id_alumno):
    return jsonify(conducta_service.estado_conducta(usuario_actual(), id_alumno))
