"""Módulo 12 (parte servidor) — Registro de tokens de notificaciones push.

POST   /dispositivos/token   registra o actualiza el token del teléfono
DELETE /dispositivos/token   lo desasocia (cierre de sesión)
"""
from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError

from app.auth import jwt_required, usuario_actual
from app.database import get_db
from app.errors import ApiError
from app.models.dispositivo import DispositivoPush
from app.utils import json_requerido, texto

bp = Blueprint("dispositivos", __name__, url_prefix="/dispositivos")
PLATAFORMAS = ("android", "ios")


@bp.post("/token")
@jwt_required()
def registrar_token():
    db = get_db()
    datos = json_requerido()
    token = texto(datos, "token", minimo=10, maximo=255)
    plataforma = texto(datos, "plataforma", minimo=3, maximo=20).lower()
    if plataforma not in PLATAFORMAS:
        raise ApiError(400, "La plataforma debe ser 'android' o 'ios'")
    id_usuario = usuario_actual()["id"]

    def _upsert() -> bool:
        fila = db.query(DispositivoPush).filter(DispositivoPush.token == token).first()
        if fila:   # mismo teléfono: se reasigna al usuario que acaba de entrar
            fila.id_usuario, fila.plataforma, fila.activo = id_usuario, plataforma, True
            return False
        db.add(DispositivoPush(id_usuario=id_usuario, token=token, plataforma=plataforma))
        return True

    try:
        creado = _upsert()
        db.commit()
    except IntegrityError:      # dos peticiones a la vez con el mismo token nuevo
        db.rollback()
        creado = _upsert()
        db.commit()

    resp = jsonify({"message": "Token registrado"})
    resp.status_code = 201 if creado else 200
    return resp


@bp.delete("/token")
@jwt_required()
def eliminar_token():
    db = get_db()
    token = texto(json_requerido(), "token", minimo=10, maximo=255)
    n = (db.query(DispositivoPush)
           .filter(DispositivoPush.token == token, DispositivoPush.id_usuario == usuario_actual()["id"])
           .update({"activo": False}))
    db.commit()
    if not n:
        raise ApiError(404, "Ese token no está registrado para tu cuenta")
    return jsonify({"message": "Token desasociado"})
