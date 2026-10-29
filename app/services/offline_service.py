"""Reglas de las operaciones hechas sin conexión (idempotencia).

Problema: sin internet, la app guarda la operación (entregar una tarea, enviar un
mensaje...) y la envía cuando vuelve la conexión. Si la red se corta justo después
de que el servidor la guardó, el celular no recibe la respuesta y la REINTENTA:
sin control, la tarea se entregaría dos veces o el mensaje saldría repetido.

Solución: la app manda en cada operación un id único (cabecera X-Id-Operacion).
La primera vez se ejecuta y se guarda su respuesta; si llega otra vez el mismo id,
se devuelve la respuesta guardada SIN volver a ejecutarla. El decorador que lo
hace está en app/offline.py.
"""
import re

import pymysql

from app.database import get_db
from app.errors import ApiError
from app.repositories import operacion_repository

# Letras, números, guion y guion bajo; de 8 a 64 caracteres (ej. un UUID).
FORMATO_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def validar_id(id_operacion: str) -> str:
    if not FORMATO_ID.match(id_operacion):
        raise ApiError(400, "X-Id-Operacion debe tener de 8 a 64 letras, números, '-' o '_'")
    return id_operacion


def respuesta_previa(usuario: dict, id_operacion: str):
    """La operación ya procesada con ese id, o None si es nueva.
    409 si ese id lo usó otro usuario (los ids deben ser únicos)."""
    previa = operacion_repository.buscar(id_operacion)
    if previa is not None and previa["id_usuario"] != usuario["id"]:
        raise ApiError(409, "Ese id de operación ya fue usado por otro usuario")
    return previa


def registrar(usuario: dict, id_operacion: str, metodo: str, ruta: str, codigo: int, respuesta: str) -> None:
    """Guarda la respuesta de una operación que salió bien (en su propia transacción)."""
    db = get_db()
    try:
        operacion_repository.guardar(id_operacion, usuario["id"], metodo, ruta, codigo, respuesta)
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()      # otro reintento con el mismo id se guardó primero: no pasa nada
    except Exception:
        db.rollback()
        raise


def consultar(usuario: dict, id_operacion: str) -> dict:
    """¿Se procesó esta operación? Para que la app sepa si debe reenviarla."""
    previa = operacion_repository.buscar(validar_id(id_operacion))
    if previa is None:
        raise ApiError(404, "Esa operación no se ha procesado")
    if previa["id_usuario"] != usuario["id"]:
        raise ApiError(403, "Esa operación no es tuya")
    return {"id_operacion": previa["id_operacion"], "metodo": previa["metodo"], "ruta": previa["ruta"],
            "codigo": previa["codigo"], "fecha": previa["fecha"]}
