"""Consultas SQL de `preferencia_notificacion`: qué notificaciones push quiere recibir
cada usuario. Si un usuario no tiene fila, recibe todas."""
from app.database import consultar_todos, consultar_uno, ejecutar

_COLUMNAS = """id_usuario, silenciar_todo, pausado_hasta, tipos_silenciados,
               no_molestar_desde, no_molestar_hasta"""


def buscar(id_usuario: int):
    return consultar_uno(f"SELECT {_COLUMNAS} FROM preferencia_notificacion WHERE id_usuario = %s",
                         (id_usuario,))


def de_usuarios(id_usuarios: list) -> list:
    """Preferencias de varios usuarios (solo los que tienen fila)."""
    if not id_usuarios:
        return []
    marcas = ", ".join(["%s"] * len(id_usuarios))
    return consultar_todos(f"SELECT {_COLUMNAS} FROM preferencia_notificacion WHERE id_usuario IN ({marcas})",
                           tuple(id_usuarios))


def guardar(id_usuario: int, silenciar_todo: bool, pausado_hasta, tipos_silenciados: str,
            no_molestar_desde, no_molestar_hasta) -> int:
    """Crea la fila del usuario o la reemplaza si ya existía (INSERT ... ON DUPLICATE KEY UPDATE)."""
    return ejecutar("""
        INSERT INTO preferencia_notificacion
            (id_usuario, silenciar_todo, pausado_hasta, tipos_silenciados,
             no_molestar_desde, no_molestar_hasta, fecha_actualizacion)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            silenciar_todo = VALUES(silenciar_todo),
            pausado_hasta = VALUES(pausado_hasta),
            tipos_silenciados = VALUES(tipos_silenciados),
            no_molestar_desde = VALUES(no_molestar_desde),
            no_molestar_hasta = VALUES(no_molestar_hasta),
            fecha_actualizacion = NOW()
    """, (id_usuario, int(silenciar_todo), pausado_hasta, tipos_silenciados,
          no_molestar_desde, no_molestar_hasta))
