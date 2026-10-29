"""Consultas SQL de la tabla `asistencia`.

La asistencia se guarda por matrícula (alumno + año) y fecha.
estado: P = presente, T = tardanza, F = falta, J = falta justificada.
"""
from app.database import consultar_todos, ejecutar, insertar


def borrar_del_dia(id_seccion: int, fecha) -> int:
    """Borra la asistencia ya registrada de una sección en una fecha (para volver
    a registrarla completa)."""
    return ejecutar("""
        DELETE a
        FROM asistencia a
        JOIN matricula m ON m.id_matricula = a.id_matricula
        WHERE m.id_seccion = %s AND a.fecha = %s
    """, (id_seccion, fecha))


def registrar(id_matricula: int, fecha, estado: str, observacion) -> int:
    return insertar("""
        INSERT INTO asistencia (id_matricula, fecha, estado, observacion)
        VALUES (%s, %s, %s, %s)
    """, (id_matricula, fecha, estado, observacion))


def de_seccion_y_fecha(id_seccion: int, fecha) -> list:
    """Asistencia de una sección en un día, con el nombre de cada alumno."""
    return consultar_todos("""
        SELECT al.id_alumno, al.apellidos, al.nombres, a.estado, a.observacion
        FROM asistencia a
        JOIN matricula m ON m.id_matricula = a.id_matricula
        JOIN alumno al ON al.id_alumno = m.id_alumno
        WHERE m.id_seccion = %s AND a.fecha = %s
        ORDER BY al.apellidos, al.nombres
    """, (id_seccion, fecha))


def de_matricula(id_matricula: int) -> list:
    """Historial de asistencia de un alumno en el año, del día más reciente al más antiguo."""
    return consultar_todos("""
        SELECT fecha, estado, observacion
        FROM asistencia
        WHERE id_matricula = %s
        ORDER BY fecha DESC
    """, (id_matricula,))


def resumen_de_matricula(id_matricula: int) -> list:
    """Cuántos días hay de cada estado: [{"estado": "P", "total": 10}, ...]"""
    return consultar_todos("""
        SELECT estado, COUNT(*) AS total
        FROM asistencia
        WHERE id_matricula = %s
        GROUP BY estado
    """, (id_matricula,))


def resumen_por_alumno(id_seccion: int, id_anio: str, desde, hasta) -> list:
    """Cuántos P, T, F y J tiene cada alumno de la sección entre dos fechas.

    SUM(a.estado = 'P') suma 1 por cada fila donde la condición es verdadera.
    El filtro de fechas va en el ON del LEFT JOIN (no en el WHERE): así el alumno
    sin registros en ese rango también sale, con 0 en todo.
    """
    return consultar_todos("""
        SELECT al.id_alumno, al.apellidos, al.nombres,
               COALESCE(SUM(a.estado = 'P'), 0) AS P,
               COALESCE(SUM(a.estado = 'T'), 0) AS T,
               COALESCE(SUM(a.estado = 'F'), 0) AS F,
               COALESCE(SUM(a.estado = 'J'), 0) AS J,
               COUNT(a.id_asistencia) AS dias
        FROM matricula m
        JOIN alumno al ON al.id_alumno = m.id_alumno
        LEFT JOIN asistencia a ON a.id_matricula = m.id_matricula
                              AND a.fecha BETWEEN %s AND %s
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s
        GROUP BY al.id_alumno, al.apellidos, al.nombres
        ORDER BY al.apellidos, al.nombres
    """, (desde, hasta, id_seccion, id_anio))
