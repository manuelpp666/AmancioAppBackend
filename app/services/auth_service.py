"""Reglas del inicio de sesión, los permisos y el cierre de sesión."""
import json

from app.auth import crear_token
from app.database import get_db
from app.errors import ApiError
from app.repositories import dispositivo_repository, usuario_repository
from app.security import verify_password
from app.utils import texto


def login(datos: dict) -> dict:
    # 1. Validar lo que llegó.
    username = texto(datos, "username", minimo=3, maximo=50)
    password = texto(datos, "password", minimo=1, maximo=200, strip=False)

    # 2. Buscar el usuario y comprobar la contraseña. Si falla cualquiera de los
    #    dos se da el mismo mensaje, para no revelar si el usuario existe.
    user = usuario_repository.buscar_por_username(username)
    if user is None or not verify_password(password, user["password_hash"]):
        raise ApiError(401, "Credenciales inválidas")

    # 3. Una cuenta desactivada no puede entrar.
    if not user["activo"]:
        raise ApiError(403, "Cuenta desactivada")

    # 4. Todo bien: se entrega el token.
    return {
        "id_usuario": user["id_usuario"],
        "username": user["username"],
        "rol": user["rol"],
        "access_token": crear_token(user),
        "token_type": "bearer",
        # Primer ingreso: si es True, la app obliga a cambiar la contraseña
        # (la inicial es el DNI) antes de dejar usar el campus.
        "debe_cambiar_password": bool(user["debe_cambiar_password"]),
    }


def mis_permisos(usuario: dict) -> dict:
    """Rol y permisos actuales, leídos de la base (por si cambiaron tras el login)."""
    user = usuario_repository.buscar_por_id(usuario["id"])
    if user is None:
        raise ApiError(401, "La cuenta ya no existe")

    permisos = None
    if user["rol"] == "ADMIN":
        texto_json = usuario_repository.permisos_de_admin(user["id_usuario"])
        permisos = json.loads(texto_json) if texto_json else None   # se guarda como texto JSON

    return {"rol": user["rol"], "activo": bool(user["activo"]), "permisos": permisos,
            "debe_cambiar_password": bool(user["debe_cambiar_password"])}


def logout(usuario: dict, datos: dict) -> dict:
    """El JWT no se puede borrar en el servidor (la app lo elimina del celular).
    Si la app envía el token de su dispositivo, se deja de enviarle notificaciones."""
    token_dispositivo = (datos.get("token_dispositivo") or "").strip()
    if token_dispositivo:
        db = get_db()
        try:
            dispositivo_repository.desactivar(token_dispositivo, usuario["id"])
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"message": "Sesión cerrada"}
