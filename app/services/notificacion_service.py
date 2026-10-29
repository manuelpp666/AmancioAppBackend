"""Reglas de las notificaciones.

Cómo se crea una notificación:
1. Un service hace algo que le interesa a alguien (el docente publica una tarea,
   el psicólogo programa una cita...) y llama a `notificar(...)` ANTES de su commit.
   Así la notificación es parte de la misma transacción: si la operación se
   deshace (rollback), la notificación también.
2. Si la petición terminó bien, después de responder se envía el aviso push al
   celular (ver `enviar_pendientes`, que llama app/__init__.py).

Tipos: TAREA, CALIFICACION, CLASE, LIBRETA, CITA, CONDUCTA, MENSAJE.
"""
import logging

from flask import g

from app import push
from app.database import get_db
from app.errors import ApiError
from app.repositories import dispositivo_repository, notificacion_repository

log = logging.getLogger(__name__)


# --- Crear notificaciones (las usan los otros services) --------------------------

def notificar(id_usuarios: list, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    """Guarda la misma notificación para varios usuarios. NO hace commit: va dentro
    de la transacción del service que la llama. Devuelve cuántas creó."""
    id_usuarios = [i for i in dict.fromkeys(id_usuarios) if i is not None]   # sin repetidos
    for id_usuario in id_usuarios:
        notificacion_repository.crear(id_usuario, tipo, titulo, mensaje[:300], id_referencia)
    if id_usuarios:
        # Se anota para enviar el push al final de la petición (si terminó bien).
        g.setdefault("push_pendientes", []).append(
            {"usuarios": id_usuarios, "titulo": titulo, "mensaje": mensaje,
             "datos": {"tipo": tipo, "id_referencia": id_referencia}})
    return len(id_usuarios)


def notificar_seccion(carga: dict, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    """Avisa a todos los alumnos de la sección de un curso."""
    alumnos = notificacion_repository.usuarios_de_seccion(carga["id_seccion"], carga["anio"])
    return notificar(alumnos, tipo, titulo, mensaje, id_referencia)


def notificar_alumno(id_alumno: int, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    return notificar([notificacion_repository.usuario_de_alumno(id_alumno)], tipo, titulo,
                     mensaje, id_referencia)


def enviar_pendientes() -> None:
    """Envía los push anotados durante la petición. Nunca lanza errores: la
    notificación ya está guardada y un fallo del push no debe romper la respuesta."""
    for aviso in g.pop("push_pendientes", []):
        try:
            tokens = dispositivo_repository.tokens_activos(aviso["usuarios"])
            push.enviar(tokens, aviso["titulo"], aviso["mensaje"], aviso["datos"])
        except Exception as error:
            log.warning("No se pudo preparar el push: %s", error)


# --- Bandeja del usuario -----------------------------------------------------------

def mis_notificaciones(usuario: dict, solo_no_leidas: bool = False) -> dict:
    return {
        "no_leidas": notificacion_repository.contar_no_leidas(usuario["id"]),
        "notificaciones": notificacion_repository.de_usuario(usuario["id"], solo_no_leidas),
    }


def marcar_leida(usuario: dict, id_notificacion: int) -> dict:
    notificacion = notificacion_repository.buscar(id_notificacion)
    if notificacion is None:
        raise ApiError(404, "Notificación no encontrada")
    if notificacion["id_usuario"] != usuario["id"]:
        raise ApiError(403, "Esa notificación no es tuya")

    db = get_db()
    try:
        notificacion_repository.marcar_leida(id_notificacion)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Notificación leída"}


def marcar_todas(usuario: dict) -> dict:
    db = get_db()
    try:
        marcadas = notificacion_repository.marcar_todas(usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Notificaciones leídas", "marcadas": marcadas}
