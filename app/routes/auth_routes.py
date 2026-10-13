"""Módulo Usuarios: iniciar sesión, consultar permisos y cerrar sesión.

POST /usuarios/login          público: usuario + contraseña → token
GET  /usuarios/mis-permisos   requiere token
POST /usuarios/logout         requiere token
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required, usuario_actual
from app.services import auth_service
from app.utils import json_requerido

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.post("/login")
def login():
    return jsonify(auth_service.login(json_requerido()))


@bp.get("/mis-permisos")
@jwt_required()
def mis_permisos():
    return jsonify(auth_service.mis_permisos(usuario_actual()))


@bp.post("/logout")
@jwt_required()
def logout():
    datos = request.get_json(silent=True) or {}   # el cuerpo es opcional
    return jsonify(auth_service.logout(usuario_actual(), datos))
