"""Autenticación con JWT (JSON Web Token).

Cómo funciona:
1. En el login, el servidor crea un token firmado con SECRET_KEY (`crear_token`).
2. La app guarda ese token y lo envía en cada petición, en la cabecera:
       Authorization: Bearer <token>
3. Las rutas protegidas usan el decorador `@jwt_required()`, que revisa el token
   antes de ejecutar la ruta. Si falta, expiró o fue alterado → error 401.

Ejemplos:
    @jwt_required()            → cualquier usuario con sesión
    @jwt_required("ALUMNO")    → solo alumnos (si no, error 403)

Dentro de la ruta, `usuario_actual()` devuelve los datos guardados en el token:
    {"sub": username, "id": id_usuario, "rol": rol, "iat": ..., "exp": ...}
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt  # librería PyJWT
from flask import g, request

from app import config
from app.errors import ApiError


def crear_token(usuario) -> str:
    """Crea el token JWT de un usuario. Dura JWT_EXPIRE_MINUTES (60 min por defecto)."""
    ahora = datetime.now(timezone.utc)
    contenido = {
        "sub": usuario.username,      # a quién pertenece el token
        "id": usuario.id_usuario,
        "rol": usuario.rol,
        "iat": ahora,                 # cuándo se creó
        "exp": ahora + timedelta(minutes=config.JWT_EXPIRE_MINUTES),  # cuándo vence
    }
    # Se firma con SECRET_KEY: si alguien cambia el contenido, la firma deja de valer.
    return jwt.encode(contenido, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def _leer_token() -> str | None:
    """Saca el token de la cabecera "Authorization: Bearer <token>"."""
    partes = request.headers.get("Authorization", "").split()
    if len(partes) == 2 and partes[0].lower() == "bearer":
        return partes[1]
    return None


def _validar_token(token: str) -> dict:
    """Comprueba la firma y la fecha de vencimiento. Devuelve el contenido del token."""
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM],
                          options={"require": ["exp", "sub"]})   # exp y sub son obligatorios
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "Token expirado", {"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise ApiError(401, "Token inválido", {"WWW-Authenticate": "Bearer"})


def jwt_required(*roles: str):
    """Decorador que protege una ruta. Si se pasan roles, solo esos roles pueden entrar."""
    def decorador(ruta):
        @wraps(ruta)   # conserva el nombre de la función original (Flask lo necesita)
        def ruta_protegida(*args, **kwargs):
            token = _leer_token()
            if not token:
                raise ApiError(401, "No se encontró el token de autenticación",
                               {"WWW-Authenticate": "Bearer"})
            datos = _validar_token(token)
            if roles and datos.get("rol") not in roles:
                raise ApiError(403, "No tienes permisos para realizar esta acción")
            g.usuario = datos   # `g` guarda datos solo durante esta petición
            return ruta(*args, **kwargs)
        return ruta_protegida
    return decorador


def usuario_actual() -> dict:
    """Datos del usuario que hizo la petición (los que venían en su token)."""
    return g.usuario


def exigir_dueno_o_roles(id_usuario: int, *roles_permitidos: str) -> None:
    """Deja pasar solo al dueño del dato (mismo id) o a uno de los roles indicados."""
    yo = usuario_actual()
    if yo["id"] != id_usuario and yo["rol"] not in roles_permitidos:
        raise ApiError(403, "No puedes acceder a información de otro usuario")
