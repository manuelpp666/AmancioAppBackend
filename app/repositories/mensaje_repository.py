"""Consultas SQL de la mensajería: tablas `conversacion` y `mensaje`.

Una conversación es entre DOS usuarios. Se guarda siempre con el id menor en
usuario1_id y el mayor en usuario2_id: así la conversación entre 3 y 8 es una
sola, la busque quien la busque.
"""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar

# El nombre de un usuario está en la ficha de su rol (alumno, docente...).
# Se une con las 5 tablas y COALESCE toma la primera que no sea NULL.
_FICHAS = """
    LEFT JOIN alumno al        ON al.id_usuario = u.id_usuario
    LEFT JOIN docente dc       ON dc.id_usuario = u.id_usuario
    LEFT JOIN administrador ad ON ad.id_usuario = u.id_usuario
    LEFT JOIN auxiliar ax      ON ax.id_usuario = u.id_usuario
    LEFT JOIN psicologo ps     ON ps.id_usuario = u.id_usuario
"""
_NOMBRE = """COALESCE(CONCAT(al.nombres, ' ', al.apellidos), CONCAT(dc.nombres, ' ', dc.apellidos),
                      CONCAT(ad.nombres, ' ', ad.apellidos), CONCAT(ax.nombres, ' ', ax.apellidos),
                      CONCAT(ps.nombres, ' ', ps.apellidos), u.username)"""


# --- Contactos (con quién puede escribir cada uno) -----------------------------------

def usuario_con_nombre(id_usuario: int):
    return consultar_uno(f"""
        SELECT u.id_usuario, u.rol, u.activo, {_NOMBRE} AS nombre
        FROM usuario u {_FICHAS}
        WHERE u.id_usuario = %s
    """, (id_usuario,))


def personal(roles: tuple, excepto: int) -> list:
    """Usuarios activos de esos roles (menos uno mismo), ordenados por rol y nombre."""
    marcas = ", ".join(["%s"] * len(roles))
    return consultar_todos(f"""
        SELECT u.id_usuario, u.rol, {_NOMBRE} AS nombre
        FROM usuario u {_FICHAS}
        WHERE u.activo = 1 AND u.id_usuario <> %s AND u.rol IN ({marcas})
        ORDER BY u.rol, nombre
    """, (excepto, *roles))


def docentes_de_seccion(id_seccion: int, id_anio: str) -> list:
    """Los docentes que dictan algún curso en la sección del alumno."""
    return consultar_todos("""
        SELECT DISTINCT u.id_usuario, u.rol, CONCAT(d.nombres, ' ', d.apellidos) AS nombre
        FROM carga_academica ca
        JOIN docente d ON d.id_docente = ca.id_docente
        JOIN usuario u ON u.id_usuario = d.id_usuario
        WHERE ca.id_seccion = %s AND ca.id_anio_escolar = %s AND u.activo = 1
        ORDER BY nombre
    """, (id_seccion, id_anio))


def alumnos_de_docente(id_docente: int, id_anio: str) -> list:
    """Los alumnos de todas las secciones donde enseña el docente."""
    return consultar_todos("""
        SELECT DISTINCT u.id_usuario, u.rol, CONCAT(a.nombres, ' ', a.apellidos) AS nombre
        FROM carga_academica ca
        JOIN matricula m ON m.id_seccion = ca.id_seccion AND m.id_anio_escolar = ca.id_anio_escolar
        JOIN alumno a ON a.id_alumno = m.id_alumno
        JOIN usuario u ON u.id_usuario = a.id_usuario
        WHERE ca.id_docente = %s AND ca.id_anio_escolar = %s AND u.activo = 1
        ORDER BY nombre
    """, (id_docente, id_anio))


# --- Conversaciones -------------------------------------------------------------

def conversaciones_de(id_usuario: int) -> list:
    """Mis conversaciones con el nombre del otro usuario y cuántos mensajes suyos no he leído.

    IF(...) elige al OTRO participante. La subconsulta cuenta, para cada
    conversación, los mensajes que me enviaron y sigo sin leer.
    """
    return consultar_todos(f"""
        SELECT c.id_conversacion, c.ultimo_mensaje, c.fecha_actualizacion,
               u.id_usuario AS id_contacto, u.rol AS rol_contacto, {_NOMBRE} AS contacto,
               (SELECT COUNT(*) FROM mensaje m
                 WHERE m.id_conversacion = c.id_conversacion
                   AND m.remitente_id <> %s AND m.leido = 0) AS no_leidos
        FROM conversacion c
        JOIN usuario u ON u.id_usuario = IF(c.usuario1_id = %s, c.usuario2_id, c.usuario1_id)
        {_FICHAS}
        WHERE c.usuario1_id = %s OR c.usuario2_id = %s
        ORDER BY c.fecha_actualizacion DESC, c.id_conversacion DESC
    """, (id_usuario, id_usuario, id_usuario, id_usuario))


def buscar_conversacion(id_conversacion: int):
    return consultar_uno("""
        SELECT id_conversacion, usuario1_id, usuario2_id, ultimo_mensaje, fecha_actualizacion
        FROM conversacion
        WHERE id_conversacion = %s
    """, (id_conversacion,))


def conversacion_entre(id_a: int, id_b: int):
    """La conversación entre dos usuarios, o None si nunca se escribieron."""
    return consultar_uno("""
        SELECT id_conversacion FROM conversacion
        WHERE usuario1_id = %s AND usuario2_id = %s
    """, (min(id_a, id_b), max(id_a, id_b)))


def crear_conversacion(id_a: int, id_b: int) -> int:
    return insertar("""
        INSERT INTO conversacion (usuario1_id, usuario2_id, fecha_actualizacion)
        VALUES (%s, %s, NOW())
    """, (min(id_a, id_b), max(id_a, id_b)))


def actualizar_ultimo(id_conversacion: int, vista_previa: str) -> int:
    """Guarda el inicio del último mensaje (para la lista de chats) y la hora."""
    return ejecutar("""
        UPDATE conversacion SET ultimo_mensaje = %s, fecha_actualizacion = NOW()
        WHERE id_conversacion = %s
    """, (vista_previa, id_conversacion))


# --- Mensajes ---------------------------------------------------------------------

def mensajes_de(id_conversacion: int) -> list:
    return consultar_todos("""
        SELECT id_mensaje, remitente_id, contenido, leido, fecha_envio
        FROM mensaje
        WHERE id_conversacion = %s
        ORDER BY fecha_envio, id_mensaje
    """, (id_conversacion,))


def crear_mensaje(id_conversacion: int, remitente_id: int, contenido: str) -> int:
    return insertar("""
        INSERT INTO mensaje (id_conversacion, remitente_id, contenido, leido, fecha_envio)
        VALUES (%s, %s, %s, 0, NOW())
    """, (id_conversacion, remitente_id, contenido))


def marcar_leidos(id_conversacion: int, id_lector: int) -> int:
    """Marca como leídos los mensajes que le enviaron al lector. Devuelve cuántos eran."""
    return ejecutar("""
        UPDATE mensaje SET leido = 1
        WHERE id_conversacion = %s AND remitente_id <> %s AND leido = 0
    """, (id_conversacion, id_lector))


def no_leidos_total(id_usuario: int) -> int:
    """Mensajes sin leer en todas mis conversaciones (para el panel de inicio)."""
    fila = consultar_uno("""
        SELECT COUNT(*) AS total
        FROM mensaje m
        JOIN conversacion c ON c.id_conversacion = m.id_conversacion
        WHERE (c.usuario1_id = %s OR c.usuario2_id = %s)
          AND m.remitente_id <> %s AND m.leido = 0
    """, (id_usuario, id_usuario, id_usuario))
    return fila["total"]
