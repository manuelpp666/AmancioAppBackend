"""Consultas SQL del horario escolar y de los recesos.

dia_semana: 1 = lunes ... 5 = viernes.
"""
from app.database import consultar_todos


def de_seccion(id_seccion: int, id_anio: str) -> list:
    """Bloques de clase de una sección (horario del alumno)."""
    return consultar_todos("""
        SELECT h.dia_semana, h.hora_inicio, h.hora_fin, c.nombre AS curso,
               CONCAT(d.nombres, ' ', d.apellidos) AS detalle
        FROM horario_escolar h
        JOIN carga_academica ca ON ca.id_carga_academica = h.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        LEFT JOIN docente d ON d.id_docente = ca.id_docente
        WHERE ca.id_seccion = %s AND ca.id_anio_escolar = %s
        ORDER BY h.dia_semana, h.hora_inicio
    """, (id_seccion, id_anio))


def de_docente(id_docente: int, id_anio: str) -> list:
    """Bloques de clase de un docente (en todas sus secciones)."""
    return consultar_todos("""
        SELECT h.dia_semana, h.hora_inicio, h.hora_fin, c.nombre AS curso,
               CONCAT(g.nombre, ' ', s.nombre, ' - ', n.nombre) AS detalle
        FROM horario_escolar h
        JOIN carga_academica ca ON ca.id_carga_academica = h.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        JOIN seccion s ON s.id_seccion = ca.id_seccion
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN nivel n ON n.id_nivel = g.id_nivel
        WHERE ca.id_docente = %s AND ca.id_anio_escolar = %s
        ORDER BY h.dia_semana, h.hora_inicio
    """, (id_docente, id_anio))


def recesos() -> list:
    return consultar_todos("""
        SELECT nombre, hora_inicio, hora_fin
        FROM receso_horario
        ORDER BY hora_inicio
    """)
