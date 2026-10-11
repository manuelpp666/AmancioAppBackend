"""JWT: creación del token y decorador de protección por rol.

Uso en una ruta:

    @bp.get("/algo")
    @jwt_required()                      # cualquier usuario con sesión
    def a(): ...

    @bp.post("/notas")
    @jwt_required("DOCENTE")             # solo ese rol (o varios: "AUXILIAR", "ADMIN")
    def b(): ...

Dentro de la ruta, `usuario_actual()` devuelve el contenido del token:
{"sub": username, "id": id_usuario, "rol": rol, "iat": ..., "exp": ...}.
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt  # PyJWT
from flask import g, request

from app import config
from app.errors import ApiError


def crear_token(usuario) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario.username,
        "id": usuario.id_usuario,
        "rol": usuario.rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def _token_de_la_cabecera() -> str | None:
    partes = request.headers.get("Authorization", "").split()
    if len(partes) == 2 and partes[0].lower() == "bearer":
        return partes[1]
    return None


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM],
                          options={"require": ["exp", "sub"]})
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "Token expirado", {"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise ApiError(401, "Token inválido", {"WWW-Authenticate": "Bearer"})


def jwt_required(*roles: str):
    def decorador(fn):
        @wraps(fn)
        def envoltura(*args, **kwargs):
            token = _token_de_la_cabecera()
            if not token:
                raise ApiError(401, "No se encontró el token de autenticación",
                               {"WWW-Authenticate": "Bearer"})
            payload = decodificar_token(token)
            if roles and payload.get("rol") not in roles:
                raise ApiError(403, "No tienes permisos para realizar esta acción")
            g.usuario = payload
            return fn(*args, **kwargs)
        return envoltura
    return decorador


def usuario_actual() -> dict:
    return g.usuario


def exigir_dueno_o_roles(id_usuario: int, *roles_privilegiados: str) -> None:
    """Solo el dueño del recurso, o un rol privilegiado, puede continuar."""
    u = usuario_actual()
    if u.get("id") != id_usuario and u.get("rol") not in roles_privilegiados:
        raise ApiError(403, "No puedes acceder a información de otro usuario")
