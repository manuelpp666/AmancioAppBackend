"""Módulo 1 — Autenticación, sesión y control por rol.

POST /usuarios/login          público
GET  /usuarios/mis-permisos   autenticado
POST /usuarios/logout         autenticado (desasocia el token push si se envía)
"""
from flask import Blueprint, jsonify, request

from app.auth import crear_token, jwt_required, usuario_actual
from app.database import get_db
from app.errors import ApiError
from app.models.dispositivo import DispositivoPush
from app.models.personal import Administrador
from app.models.usuario import Usuario
from app.security import verify_password
from app.services import seguridad
from app.services.colegio import exigir_cambio_password, exigir_correo
from app.services.contacto import tiene_correo
from app.utils import json_requerido, texto

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.post("/login")
def login():
    db = get_db()
    datos = json_requerido()
    username = texto(datos, "username", minimo=3, maximo=50)
    password = texto(datos, "password", minimo=1, maximo=200, strip=False)

    # 0. Freno a la prueba de contraseñas: va ANTES de verificar nada, para que
    #    cada intento bloqueado no cueste una verificación de bcrypt.
    espera = seguridad.segundos_de_bloqueo(db, username, seguridad.ip_de_la_peticion())
    if espera > 0:
        seguridad.anotar(db, username, False, "BLOQUEADO")
        minutos = max(1, round(espera / 60))
        raise ApiError(429, f"Demasiados intentos fallidos. Vuelve a intentarlo en {minutos} minuto(s).",
                       {"Retry-After": str(espera)})

    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        seguridad.anotar(db, username, False, "USUARIO_NO_EXISTE")
        raise ApiError(401, "Credenciales inválidas")

    if not verify_password(password, user.password_hash):
        seguridad.anotar(db, username, False, "PASSWORD_INCORRECTA", user.id_usuario, user.rol)
        raise ApiError(401, "Credenciales inválidas")

    if not user.activo:
        seguridad.anotar(db, username, False, "CUENTA_DESACTIVADA", user.id_usuario, user.rol)
        raise ApiError(403, "Cuenta desactivada")

    seguridad.anotar(db, username, True, None, user.id_usuario, user.rol)

    permisos = None
    if user.rol == "ADMIN":
        admin = db.query(Administrador).filter(Administrador.id_usuario == user.id_usuario).first()
        permisos = admin.permisos if admin else None

    return jsonify({
        "id_usuario": user.id_usuario,
        "username": user.username,
        "rol": user.rol,
        "access_token": crear_token(user),
        "token_type": "bearer",
        "status": "success",
        "permisos": permisos,
        # La app obliga a cambiar la clave inicial (el DNI) antes de usar el campus.
        "debe_cambiar_password": bool(user.debe_cambiar_password) and exigir_cambio_password(db),
        "debe_registrar_correo": exigir_correo(db) and not tiene_correo(db, user),
    })


@bp.get("/mis-permisos")
@jwt_required()
def mis_permisos():
    """Rol y permisos que el usuario tiene AHORA en la base (no los del token)."""
    db = get_db()
    user = db.query(Usuario).filter(Usuario.id_usuario == usuario_actual()["id"]).first()
    if not user:
        raise ApiError(401, "La cuenta ya no existe")
    permisos = None
    if user.rol == "ADMIN":
        admin = db.query(Administrador).filter(Administrador.id_usuario == user.id_usuario).first()
        permisos = admin.permisos if admin else None
    return jsonify({"rol": user.rol, "activo": bool(user.activo), "permisos": permisos})


@bp.post("/logout")
@jwt_required()
def logout():
    """El JWT no se puede 'borrar' del servidor: la app lo elimina del teléfono.
    Aquí solo se desasocia el token de notificaciones de este dispositivo."""
    datos = request.get_json(silent=True) or {}
    token_dispositivo = (datos.get("token_dispositivo") or "").strip()
    if token_dispositivo:
        db = get_db()
        (db.query(DispositivoPush)
           .filter(DispositivoPush.token == token_dispositivo,
                   DispositivoPush.id_usuario == usuario_actual()["id"])
           .update({"activo": False}))
        db.commit()
    return jsonify({"message": "Sesión cerrada"})
