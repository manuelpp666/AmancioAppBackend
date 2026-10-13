"""Módulo Dispositivos: token de notificaciones push del celular.

POST   /dispositivos/token   registrar (201 si es nuevo, 200 si ya existía)
DELETE /dispositivos/token   dejar de enviar notificaciones a ese celular
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import dispositivo_service
from app.utils import json_requerido

bp = Blueprint("dispositivos", __name__, url_prefix="/dispositivos")


@bp.post("/token")
@jwt_required()
def registrar_token():
    respuesta, codigo = dispositivo_service.registrar(usuario_actual(), json_requerido())
    return jsonify(respuesta), codigo


@bp.delete("/token")
@jwt_required()
def eliminar_token():
    return jsonify(dispositivo_service.eliminar(usuario_actual(), json_requerido()))
