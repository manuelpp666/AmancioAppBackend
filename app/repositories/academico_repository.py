"""Consultas SQL de la estructura académica: año escolar, bimestres, grados,
secciones y cursos."""
from app.database import consultar_todos, consultar_uno


def anio_activo():
    """El año escolar marcado como activo, o None."""
    return consultar_uno("""
        SELECT id_anio_escolar, fecha_inicio, fecha_fin, tipo
        FROM anio_escolar
        WHERE activo = 1
        LIMIT 1
    """)


def bimestres(id_anio: str) -> list:
    return consultar_todos("""
        SELECT numero, fecha_inicio, fecha_fin
        FROM bimestre
        WHERE id_anio_escolar = %s
        ORDER BY numero
    """, (id_anio,))


def bimestre_de_fecha(id_anio: str, dia):
    """Bimestre en el que cae una fecha. Si cae en vacaciones entre bimestres,
    devuelve el último que ya empezó. None si el año aún no empezó."""
    return consultar_uno("""
        SELECT numero, fecha_inicio, fecha_fin
        FROM bimestre
        WHERE id_anio_escolar = %s AND fecha_inicio <= %s
        ORDER BY numero DESC
        LIMIT 1
    """, (id_anio, dia))


def grados_con_nivel() -> list:
    """Todos los grados con el nombre de su nivel, en orden."""
    return consultar_todos("""
        SELECT n.id_nivel, n.nombre AS nivel, g.id_grado, g.nombre
        FROM grado g
        JOIN nivel n ON n.id_nivel = g.id_nivel
        ORDER BY n.id_nivel, g.orden
    """)


def secciones(id_anio: str, id_grado=None) -> list:
    """Secciones de un año. Si se indica id_grado, solo las de ese grado."""
    sql = """
        SELECT s.id_seccion, s.nombre, s.vacantes, s.id_grado,
               g.nombre AS grado, n.nombre AS nivel
        FROM seccion s
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN nivel n ON n.id_nivel = g.id_nivel
        WHERE s.id_anio_escolar = %s
    """
    params = [id_anio]
    if id_grado is not None:          # filtro opcional
        sql += " AND s.id_grado = %s"
        params.append(id_grado)
    sql += " ORDER BY g.orden, s.nombre"
    return consultar_todos(sql, tuple(params))


def seccion_por_id(id_seccion: int):
    return consultar_uno("""
        SELECT s.id_seccion, s.nombre, s.id_anio_escolar, g.nombre AS grado, n.nombre AS nivel
        FROM seccion s
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN nivel n ON n.id_nivel = g.id_nivel
        WHERE s.id_seccion = %s
    """, (id_seccion,))


def cursos() -> list:
    return consultar_todos("""
        SELECT c.id_curso, c.nombre, a.nombre AS area
        FROM curso c
        LEFT JOIN area a ON a.id_area = c.id_area
        ORDER BY c.nombre
    """)
