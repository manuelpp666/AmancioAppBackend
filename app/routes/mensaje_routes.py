"""Módulo Mensajería interna (chat entre dos usuarios).

GET   /mensajes/contactos                      con quién puedo iniciar una conversación
GET   /mensajes/conversaciones                 mis conversaciones (último mensaje y no leídos)
POST  /mensajes/conversaciones                 escribir a un contacto (201 nueva / 200 ya existía)
GET   /mensajes/conversaciones/<id>            los mensajes de una conversación
GET   /mensajes/conversaciones/<id>?desde=<id_mensaje>   solo los mensajes NUEVOS (tiempo real)
POST  /mensajes/conversaciones/<id>            responder en una conversación
PATCH /mensajes/conversaciones/<id>/leido      marcar como leídos los mensajes recibidos

JSON:
    iniciar:   {"id_usuario": 5, "contenido": "Hola profesor..."}
    responder: {"contenido": "..."}
Los POST aceptan la cabecera X-Id-Operacion (envío sin conexión, ver app/offline.py).

TIEMPO REAL: con el chat abierto, la app pregunta cada pocos segundos por los mensajes
nuevos (?desde=<id del último mensaje que tiene>). La respuesta es pequeña: solo lo
nuevo y `leidos_hasta` (hasta qué mensaje mío ya leyó el otro, para el "leído").
Con la app cerrada, el aviso llega como notificación push.
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.offline import idempotente
from app.services import mensaje_service
from app.utils import json_requerido

bp = Blueprint("mensajes", __name__, url_prefix="/mensajes")


@bp.get("/contactos")
@jwt_required()
def contactos():
    return jsonify(mensaje_service.contactos(usuario_actual()))


@bp.get("/conversaciones")
@jwt_required()
def conversaciones():
    return jsonify(mensaje_service.conversaciones(usuario_actual()))


@bp.post("/conversaciones")
@jwt_required()
@idempotente
def iniciar():
    respuesta, codigo = mensaje_service.iniciar(usuario_actual(), json_requerido())
    return jsonify(respuesta), codigo


@bp.get("/conversaciones/<int:id_conversacion>")
@jwt_required()
def ver(id_conversacion):
    desde = request.args.get("desde", type=int)      # None = toda la conversación
    return jsonify(mensaje_service.ver(usuario_actual(), id_conversacion, desde))


@bp.post("/conversaciones/<int:id_conversacion>")
@jwt_required()
@idempotente
def enviar(id_conversacion):
    return jsonify(mensaje_service.enviar(usuario_actual(), id_conversacion, json_requerido())), 201


@bp.patch("/conversaciones/<int:id_conversacion>/leido")
@jwt_required()
def marcar_leidos(id_conversacion):
    return jsonify(mensaje_service.marcar_leidos(usuario_actual(), id_conversacion))
