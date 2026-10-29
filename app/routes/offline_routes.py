"""Módulo Sin conexión (offline).

GET /offline/operaciones/<id_operacion>   ¿la API ya procesó esta operación? (200 sí / 404 no)

Las operaciones se envían con la cabecera X-Id-Operacion a las rutas marcadas con
@idempotente (ver app/offline.py): entregar tarea, asistencia por lote, reporte de
conducta, solicitar cita, registrar notas y enviar mensajes.
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import offline_service

bp = Blueprint("offline", __name__, url_prefix="/offline")


@bp.get("/operaciones/<id_operacion>")
@jwt_required()
def consultar_operacion(id_operacion):
    return jsonify(offline_service.consultar(usuario_actual(), id_operacion))
