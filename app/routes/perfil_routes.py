"""Módulo Perfil: ver los datos propios y la matrícula, editarlos y cambiar la contraseña.

GET   /perfil/mi-perfil/<username>            el propio, o cualquiera si es ADMIN
GET   /perfil/mi-matricula                    ALUMNO: nivel, grado, sección y condición del año activo
PATCH /perfil/contacto/<username>             teléfono y/o correo
PATCH /perfil/alumno/<username>/direccion     solo ALUMNO
PATCH /perfil/alumno/<username>/medicos       solo ALUMNO
POST  /perfil/auth/change-password            cambiar la contraseña (también en el primer ingreso)
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.services import perfil_service
from app.utils import json_requerido

bp = Blueprint("perfil", __name__, url_prefix="/perfil")


@bp.get("/mi-perfil/<username>")
@jwt_required()
def mi_perfil(username):
    return jsonify(perfil_service.ver_perfil(usuario_actual(), username))


@bp.get("/mi-matricula")
@jwt_required("ALUMNO")
def mi_matricula():
    return jsonify(perfil_service.ver_matricula(usuario_actual()))


@bp.patch("/contacto/<username>")
@jwt_required()
def actualizar_contacto(username):
    return jsonify(perfil_service.actualizar_contacto(usuario_actual(), username, json_requerido()))


@bp.patch("/alumno/<username>/direccion")
@jwt_required("ALUMNO")
def actualizar_direccion(username):
    return jsonify(perfil_service.actualizar_direccion(usuario_actual(), username, json_requerido()))


@bp.patch("/alumno/<username>/medicos")
@jwt_required("ALUMNO")
def actualizar_medicos(username):
    return jsonify(perfil_service.actualizar_medicos(usuario_actual(), username, json_requerido()))


@bp.post("/auth/change-password")
@jwt_required()
def change_password():
    return jsonify(perfil_service.cambiar_password(usuario_actual(), json_requerido()))
