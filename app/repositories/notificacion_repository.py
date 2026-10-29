"""Consultas SQL de la tabla `notificacion` (bandeja de avisos de cada usuario)."""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar


def crear(id_usuario: int, tipo: str, titulo: str, mensaje: str, id_referencia) -> int:
    return insertar("""
        INSERT INTO notificacion (id_usuario, tipo, titulo, mensaje, id_referencia, leida)
        VALUES (%s, %s, %s, %s, %s, 0)
    """, (id_usuario, tipo, titulo, mensaje, id_referencia))


def de_usuario(id_usuario: int, solo_no_leidas: bool, limite: int = 50) -> list:
    """Notificaciones del usuario, la más reciente primero."""
    sql = """
        SELECT id_notificacion, tipo, titulo, mensaje, id_referencia, leida, fecha
        FROM notificacion
        WHERE id_usuario = %s
    """
    if solo_no_leidas:
        sql += " AND leida = 0"
    sql += " ORDER BY fecha DESC, id_notificacion DESC LIMIT %s"
    return consultar_todos(sql, (id_usuario, limite))


def contar_no_leidas(id_usuario: int) -> int:
    fila = consultar_uno("SELECT COUNT(*) AS total FROM notificacion WHERE id_usuario = %s AND leida = 0",
                         (id_usuario,))
    return fila["total"]


def buscar(id_notificacion: int):
    return consultar_uno("SELECT id_notificacion, id_usuario, leida FROM notificacion WHERE id_notificacion = %s",
                         (id_notificacion,))


def marcar_leida(id_notificacion: int) -> int:
    return ejecutar("UPDATE notificacion SET leida = 1 WHERE id_notificacion = %s", (id_notificacion,))


def marcar_todas(id_usuario: int) -> int:
    """Marca como leídas todas las pendientes del usuario. Devuelve cuántas eran."""
    return ejecutar("UPDATE notificacion SET leida = 1 WHERE id_usuario = %s AND leida = 0",
                    (id_usuario,))


# --- A quién avisar -----------------------------------------------------------

def usuarios_de_seccion(id_seccion: int, id_anio: str) -> list:
    """Cuentas (id_usuario) de los alumnos matriculados en una sección."""
    filas = consultar_todos("""
        SELECT a.id_usuario
        FROM matricula m
        JOIN alumno a ON a.id_alumno = m.id_alumno
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s AND a.id_usuario IS NOT NULL
    """, (id_seccion, id_anio))
    return [fila["id_usuario"] for fila in filas]


def usuario_de_alumno(id_alumno: int):
    fila = consultar_uno("SELECT id_usuario FROM alumno WHERE id_alumno = %s", (id_alumno,))
    return fila["id_usuario"] if fila else None
