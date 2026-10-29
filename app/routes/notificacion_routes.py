"""Módulo Notificaciones: la bandeja de avisos de cada usuario.

GET   /notificaciones?solo_no_leidas=1      mis notificaciones (las 50 más recientes)
PATCH /notificaciones/<id>/leida            marcar una como leída (solo las propias)
PATCH /notificaciones/leer-todas            marcar todas como leídas

Las notificaciones las crean los otros módulos (nueva tarea, calificación, cita
programada, nuevo mensaje...). Ver app/services/notificacion_service.py.
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.services import notificacion_service

bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")


@bp.get("")
@jwt_required()
def mis_notificaciones():
    solo_no_leidas = request.args.get("solo_no_leidas") in ("1", "true")
    return jsonify(notificacion_service.mis_notificaciones(usuario_actual(), solo_no_leidas))


@bp.patch("/<int:id_notificacion>/leida")
@jwt_required()
def marcar_leida(id_notificacion):
    return jsonify(notificacion_service.marcar_leida(usuario_actual(), id_notificacion))


@bp.patch("/leer-todas")
@jwt_required()
def marcar_todas():
    return jsonify(notificacion_service.marcar_todas(usuario_actual()))
