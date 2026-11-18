"""Módulo Notificaciones: la bandeja de avisos de cada usuario.

GET   /notificaciones?solo_no_leidas=1      mis notificaciones (las 50 más recientes)
PATCH /notificaciones/<id>/leida            marcar una como leída (solo las propias)
PATCH /notificaciones/leer-todas            marcar todas como leídas
GET   /notificaciones/contadores            {mensajes_no_leidos, notificaciones_no_leidas} (globos del menú)
GET   /notificaciones/preferencias          qué notificaciones push recibo (y los tipos que existen)
PUT   /notificaciones/preferencias          silenciar o limitar las notificaciones push

JSON de preferencias (todo opcional; lo que no se envía queda igual):
    {"silenciar_todo": false, "tipos_silenciados": ["CLASE"], "pausar_horas": 8,
     "no_molestar_desde": "22:00", "no_molestar_hasta": "07:00"}

Las notificaciones las crean los otros módulos (nueva tarea, calificación, cita
programada, nuevo mensaje...). Ver app/services/notificacion_service.py.
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.services import notificacion_service
from app.utils import json_requerido

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


@bp.get("/contadores")
@jwt_required()
def contadores():
    """Solo los números de no leídos (la app los pide cada pocos segundos para los globos)."""
    return jsonify(notificacion_service.contadores(usuario_actual()))


@bp.get("/preferencias")
@jwt_required()
def preferencias():
    return jsonify(notificacion_service.preferencias(usuario_actual()))


@bp.put("/preferencias")
@jwt_required()
def guardar_preferencias():
    return jsonify(notificacion_service.guardar_preferencias(usuario_actual(), json_requerido()))
