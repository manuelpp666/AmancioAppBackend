"""Consultas SQL de la tabla `dispositivo_push` (tokens de notificaciones)."""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar


def buscar_por_token(token: str):
    return consultar_uno("""
        SELECT id_dispositivo, id_usuario, token, plataforma, activo
        FROM dispositivo_push
        WHERE token = %s
    """, (token,))


def crear(id_usuario: int, token: str, plataforma: str) -> int:
    return insertar("""
        INSERT INTO dispositivo_push (id_usuario, token, plataforma, activo)
        VALUES (%s, %s, %s, 1)
    """, (id_usuario, token, plataforma))


def reasignar(id_dispositivo: int, id_usuario: int, plataforma: str) -> int:
    """El celular pasa a ser del usuario que acaba de iniciar sesión, y se reactiva."""
    return ejecutar("""
        UPDATE dispositivo_push
        SET id_usuario = %s, plataforma = %s, activo = 1, fecha_actualizacion = NOW()
        WHERE id_dispositivo = %s
    """, (id_usuario, plataforma, id_dispositivo))


def desactivar(token: str, id_usuario: int) -> int:
    """Deja de enviar notificaciones a ese celular (solo si es del usuario)."""
    return ejecutar("""
        UPDATE dispositivo_push
        SET activo = 0, fecha_actualizacion = NOW()
        WHERE token = %s AND id_usuario = %s
    """, (token, id_usuario))


def tokens_activos(id_usuarios: list) -> list:
    """Tokens de los celulares activos de esos usuarios (para enviarles una notificación push)."""
    if not id_usuarios:
        return []
    marcas = ", ".join(["%s"] * len(id_usuarios))      # un %s por cada usuario
    filas = consultar_todos(f"""
        SELECT token FROM dispositivo_push
        WHERE activo = 1 AND id_usuario IN ({marcas})
    """, tuple(id_usuarios))
    return [fila["token"] for fila in filas]
