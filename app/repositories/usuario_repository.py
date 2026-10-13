"""Consultas SQL de la tabla `usuario` (cuentas de acceso)."""
from app.database import consultar_uno, ejecutar, insertar


def buscar_por_username(username: str):
    return consultar_uno("""
        SELECT id_usuario, username, password_hash, rol, activo, debe_cambiar_password
        FROM usuario
        WHERE username = %s
    """, (username,))


def buscar_por_id(id_usuario: int):
    return consultar_uno("""
        SELECT id_usuario, username, password_hash, rol, activo, debe_cambiar_password
        FROM usuario
        WHERE id_usuario = %s
    """, (id_usuario,))


def crear(username: str, password_hash: str, rol: str, debe_cambiar_password: bool) -> int:
    return insertar("""
        INSERT INTO usuario (username, password_hash, rol, activo, debe_cambiar_password)
        VALUES (%s, %s, %s, 1, %s)
    """, (username, password_hash, rol, debe_cambiar_password))


def cambiar_password(id_usuario: int, password_hash: str) -> int:
    """Guarda la clave nueva y apaga la marca de "primer ingreso"."""
    return ejecutar("""
        UPDATE usuario
        SET password_hash = %s, debe_cambiar_password = 0
        WHERE id_usuario = %s
    """, (password_hash, id_usuario))


def permisos_de_admin(id_usuario: int):
    """Permisos del administrador (texto JSON), o None si no es admin."""
    fila = consultar_uno("SELECT permisos FROM administrador WHERE id_usuario = %s",
                         (id_usuario,))
    return fila["permisos"] if fila else None
