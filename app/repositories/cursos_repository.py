"""Consultas SQL de los cursos (cargas académicas) y de las matrículas.

Un "curso" de la app es una fila de `carga_academica`: un curso dictado por un
docente en una sección durante un año.
"""
from app.database import consultar_todos, consultar_uno

# Datos completos de un curso: se une la carga académica con el curso, el área,
# la sección, el grado, el nivel y el docente. Lo usan varias consultas.
_SELECT_CURSO = """
    SELECT ca.id_carga_academica, ca.id_curso, c.nombre AS curso, a.nombre AS area,
           ca.id_seccion, s.nombre AS seccion, g.nombre AS grado, n.nombre AS nivel,
           ca.id_anio_escolar AS anio, ca.id_docente,
           CONCAT(d.nombres, ' ', d.apellidos) AS docente
    FROM carga_academica ca
    JOIN curso c ON c.id_curso = ca.id_curso
    LEFT JOIN area a ON a.id_area = c.id_area
    JOIN seccion s ON s.id_seccion = ca.id_seccion
    JOIN grado g ON g.id_grado = s.id_grado
    JOIN nivel n ON n.id_nivel = g.id_nivel
    LEFT JOIN docente d ON d.id_docente = ca.id_docente
"""


def buscar_carga(id_carga: int):
    return consultar_uno(_SELECT_CURSO + " WHERE ca.id_carga_academica = %s", (id_carga,))


def cursos_de_seccion(id_seccion: int, id_anio: str) -> list:
    return consultar_todos(_SELECT_CURSO + """
        WHERE ca.id_seccion = %s AND ca.id_anio_escolar = %s
        ORDER BY c.nombre
    """, (id_seccion, id_anio))


def cursos_de_docente(id_docente: int, id_anio: str) -> list:
    return consultar_todos(_SELECT_CURSO + """
        WHERE ca.id_docente = %s AND ca.id_anio_escolar = %s
        ORDER BY g.orden, s.nombre, c.nombre
    """, (id_docente, id_anio))


def matricula_del_anio(id_alumno: int, id_anio: str):
    """Matrícula del alumno en ese año, o None si no está matriculado."""
    return consultar_uno("""
        SELECT id_matricula, id_alumno, id_seccion, id_grado, estado, condicion
        FROM matricula
        WHERE id_alumno = %s AND id_anio_escolar = %s
    """, (id_alumno, id_anio))


def alumnos_de_seccion(id_seccion: int, id_anio: str) -> list:
    """Alumnos matriculados en una sección, ordenados por apellido."""
    return consultar_todos("""
        SELECT a.id_alumno, m.id_matricula, a.dni, a.nombres, a.apellidos
        FROM matricula m
        JOIN alumno a ON a.id_alumno = m.id_alumno
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s
        ORDER BY a.apellidos, a.nombres
    """, (id_seccion, id_anio))
