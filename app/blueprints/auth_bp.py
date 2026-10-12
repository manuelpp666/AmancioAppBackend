"""Módulo Usuarios: iniciar sesión, consultar permisos y cerrar sesión.

POST /usuarios/login          público: usuario + contraseña → token
GET  /usuarios/mis-permisos   requiere token
POST /usuarios/logout         requiere token
"""
from flask import Blueprint, jsonify, request

from app.auth import crear_token, jwt_required, usuario_actual
from app.database import get_db
from app.errors import ApiError
from app.models.dispositivo import DispositivoPush
from app.models.personal import Administrador
from app.models.usuario import Usuario
from app.security import verify_password
from app.utils import json_requerido, texto

# Todas las rutas de este archivo empiezan con /usuarios
bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.post("/login")
def login():
    db = get_db()

    # 1. Leer el usuario y la contraseña del JSON enviado.
    datos = json_requerido()
    username = texto(datos, "username", minimo=3, maximo=50)
    password = texto(datos, "password", minimo=1, maximo=200, strip=False)

    # 2. Buscar el usuario y comprobar la contraseña.
    #    Si falla cualquiera de los dos se da el mismo mensaje, para no revelar
    #    si el usuario existe o no.
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise ApiError(401, "Credenciales inválidas")

    # 3. Una cuenta desactivada no puede entrar.
    if not user.activo:
        raise ApiError(403, "Cuenta desactivada")

    # 4. Todo bien: devolver el token. La app lo enviará en cada petición.
    return jsonify({
        "id_usuario": user.id_usuario,
        "username": user.username,
        "rol": user.rol,
        "access_token": crear_token(user),
        "token_type": "bearer",
    })


@bp.get("/mis-permisos")
@jwt_required()
def mis_permisos():
    """Rol y permisos actuales del usuario, leídos de la base (no del token,
    por si cambiaron después de iniciar sesión)."""
    db = get_db()
    user = db.get(Usuario, usuario_actual()["id"])   # buscar por clave primaria
    if user is None:
        raise ApiError(401, "La cuenta ya no existe")

    # Solo los administradores tienen una lista de permisos.
    permisos = None
    if user.rol == "ADMIN":
        admin = db.query(Administrador).filter(Administrador.id_usuario == user.id_usuario).first()
        if admin is not None:
            permisos = admin.permisos

    return jsonify({"rol": user.rol, "activo": bool(user.activo), "permisos": permisos})


@bp.post("/logout")
@jwt_required()
def logout():
    """Cerrar sesión.

    Un JWT no se puede "borrar" en el servidor: es la app la que lo elimina del
    celular. Lo único que se hace aquí es dejar de enviar notificaciones a ese
    celular, si la app manda su token de dispositivo (es opcional).
    """
    datos = request.get_json(silent=True) or {}
    token_dispositivo = (datos.get("token_dispositivo") or "").strip()

    if token_dispositivo:
        db = get_db()
        dispositivo = (db.query(DispositivoPush)
                       .filter(DispositivoPush.token == token_dispositivo,
                               DispositivoPush.id_usuario == usuario_actual()["id"])
                       .first())
        if dispositivo is not None:
            dispositivo.activo = False
            db.commit()

    return jsonify({"message": "Sesión cerrada"})
