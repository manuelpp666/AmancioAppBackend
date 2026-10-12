"""Módulo Dispositivos: guardar el token de notificaciones push del celular.

POST   /dispositivos/token   registrar (o actualizar) el token del celular
DELETE /dispositivos/token   dejar de enviar notificaciones a ese celular
"""
from flask import Blueprint, jsonify

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

    dispositivo = db.query(DispositivoPush).filter(DispositivoPush.token == token).first()

    if dispositivo is None:
        # Celular nuevo: se crea el registro → 201 (creado).
        db.add(DispositivoPush(id_usuario=id_usuario, token=token, plataforma=plataforma))
        codigo = 201
    else:
        # Celular ya conocido: pasa a ser del usuario actual (puede que antes
        # lo usara otra persona) y se vuelve a activar → 200 (ok).
        dispositivo.id_usuario = id_usuario
        dispositivo.plataforma = plataforma
        dispositivo.activo = True
        codigo = 200

    db.commit()
    return jsonify({"message": "Token registrado"}), codigo


@bp.delete("/token")
@jwt_required()
def eliminar_token():
    db = get_db()
    token = texto(json_requerido(), "token", minimo=10, maximo=255)

    # Solo se puede desactivar un token propio.
    dispositivo = (db.query(DispositivoPush)
                   .filter(DispositivoPush.token == token,
                           DispositivoPush.id_usuario == usuario_actual()["id"])
                   .first())
    if dispositivo is None:
        raise ApiError(404, "Ese token no está registrado para tu cuenta")

    dispositivo.activo = False   # no se borra: solo se deja de usar
    db.commit()
    return jsonify({"message": "Token desasociado"})
