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
