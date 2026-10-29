"""Consultas SQL de la tabla `operacion_offline` (operaciones ya procesadas)."""
from app.database import consultar_uno, insertar


def buscar(id_operacion: str):
    return consultar_uno("""
        SELECT id_operacion, id_usuario, metodo, ruta, codigo, respuesta, fecha
        FROM operacion_offline
        WHERE id_operacion = %s
    """, (id_operacion,))


def guardar(id_operacion: str, id_usuario: int, metodo: str, ruta: str, codigo: int, respuesta: str) -> int:
    return insertar("""
        INSERT INTO operacion_offline (id_operacion, id_usuario, metodo, ruta, codigo, respuesta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (id_operacion, id_usuario, metodo, ruta, codigo, respuesta))
