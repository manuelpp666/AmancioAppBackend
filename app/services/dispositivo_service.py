"""Reglas del token de notificaciones push de cada celular."""
from app.database import get_db
from app.errors import ApiError
from app.repositories import dispositivo_repository
from app.utils import texto

PLATAFORMAS = ("android", "ios")


def registrar(usuario: dict, datos: dict) -> tuple[dict, int]:
    """Guarda el token. Devuelve (respuesta, código): 201 si es nuevo, 200 si ya existía."""
    token = texto(datos, "token", minimo=10, maximo=255)
    plataforma = texto(datos, "plataforma", minimo=3, maximo=20).lower()
    if plataforma not in PLATAFORMAS:
        raise ApiError(400, "La plataforma debe ser 'android' o 'ios'")

    existente = dispositivo_repository.buscar_por_token(token)

    db = get_db()
    try:
        if existente is None:
            dispositivo_repository.crear(usuario["id"], token, plataforma)
            codigo = 201
        else:
            # Celular ya conocido: pasa al usuario actual (puede que antes lo
            # usara otra persona) y se vuelve a activar.
            dispositivo_repository.reasignar(existente["id_dispositivo"], usuario["id"], plataforma)
            codigo = 200
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Token registrado"}, codigo


def eliminar(usuario: dict, datos: dict) -> dict:
    token = texto(datos, "token", minimo=10, maximo=255)

    db = get_db()
    try:
        # Solo se desactiva si el token es del usuario (el WHERE lo comprueba).
        filas = dispositivo_repository.desactivar(token, usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    if filas == 0:
        raise ApiError(404, "Ese token no está registrado para tu cuenta")
    return {"message": "Token desasociado"}
