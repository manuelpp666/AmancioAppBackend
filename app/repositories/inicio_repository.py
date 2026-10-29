"""Consultas SQL del panel de inicio (resúmenes para la primera pantalla de la app).

Lo que ya existe en otros repositories (horario, asistencia, citas...) se reutiliza
desde el service; aquí solo están las consultas propias del panel.
"""
from app.database import consultar_todos, consultar_uno


# --- Alumno -----------------------------------------------------------------------

def proximas_tareas(id_alumno: int, id_seccion: int, id_anio: str, limite: int = 5) -> list:
    """Tareas de sus cursos que aún NO entregó y cuya fecha límite no pasó.
    LEFT JOIN + "e.id_entrega IS NULL" = las que no tienen entrega de ese alumno."""
    return consultar_todos("""
        SELECT t.id_tarea, t.titulo, t.fecha_entrega, c.nombre AS curso, ca.id_carga_academica
        FROM tarea t
        JOIN carga_academica ca ON ca.id_carga_academica = t.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        LEFT JOIN entrega_tarea e ON e.id_tarea = t.id_tarea AND e.id_alumno = %s
        WHERE ca.id_seccion = %s AND ca.id_anio_escolar = %s
          AND t.fecha_entrega >= NOW() AND e.id_entrega IS NULL
        ORDER BY t.fecha_entrega
        LIMIT %s
    """, (id_alumno, id_seccion, id_anio, limite))


def ultimas_notas(id_matricula: int, limite: int = 5) -> list:
    return consultar_todos("""
        SELECT c.nombre AS curso, n.bimestre, n.tipo_nota AS evaluacion, n.valor, n.fecha_registro
        FROM nota n
        JOIN curso c ON c.id_curso = n.id_curso
        WHERE n.id_matricula = %s
        ORDER BY n.fecha_registro DESC, n.id_nota DESC
        LIMIT %s
    """, (id_matricula, limite))


def proximas_clases_de_seccion(id_seccion: int, id_anio: str, limite: int = 3) -> list:
    return consultar_todos("""
        SELECT cv.id_clase_virtual, cv.tema, cv.fecha, cv.enlace, c.nombre AS curso
        FROM clase_virtual cv
        JOIN carga_academica ca ON ca.id_carga_academica = cv.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        WHERE ca.id_seccion = %s AND ca.id_anio_escolar = %s AND cv.fecha >= NOW()
        ORDER BY cv.fecha
        LIMIT %s
    """, (id_seccion, id_anio, limite))


# --- Docente ------------------------------------------------------------------------

def entregas_por_calificar(id_docente: int, id_anio: str) -> list:
    """Por cada tarea de sus cursos, cuántas entregas faltan calificar (solo las que tienen alguna)."""
    return consultar_todos("""
        SELECT t.id_tarea, t.titulo, c.nombre AS curso, CONCAT(g.nombre, ' ', s.nombre) AS seccion,
               COUNT(e.id_entrega) AS por_calificar
        FROM tarea t
        JOIN carga_academica ca ON ca.id_carga_academica = t.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        JOIN seccion s ON s.id_seccion = ca.id_seccion
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN entrega_tarea e ON e.id_tarea = t.id_tarea AND e.calificacion IS NULL
        WHERE ca.id_docente = %s AND ca.id_anio_escolar = %s
        GROUP BY t.id_tarea, t.titulo, c.nombre, g.nombre, s.nombre
        ORDER BY t.fecha_entrega
    """, (id_docente, id_anio))


def proximas_clases_de_docente(id_docente: int, id_anio: str, limite: int = 3) -> list:
    return consultar_todos("""
        SELECT cv.id_clase_virtual, cv.tema, cv.fecha, cv.enlace, c.nombre AS curso,
               CONCAT(g.nombre, ' ', s.nombre) AS seccion
        FROM clase_virtual cv
        JOIN carga_academica ca ON ca.id_carga_academica = cv.id_carga_academica
        JOIN curso c ON c.id_curso = ca.id_curso
        JOIN seccion s ON s.id_seccion = ca.id_seccion
        JOIN grado g ON g.id_grado = s.id_grado
        WHERE ca.id_docente = %s AND ca.id_anio_escolar = %s AND cv.fecha >= NOW()
        ORDER BY cv.fecha
        LIMIT %s
    """, (id_docente, id_anio, limite))


# --- Auxiliar -----------------------------------------------------------------------

def secciones_sin_asistencia(id_anio: str, dia) -> list:
    """Secciones con alumnos matriculados que todavía no tienen asistencia ese día.
    NOT EXISTS: se queda con las secciones para las que la subconsulta no encuentra nada."""
    return consultar_todos("""
        SELECT s.id_seccion, CONCAT(g.nombre, ' ', s.nombre, ' - ', n.nombre) AS seccion,
               COUNT(m.id_matricula) AS alumnos
        FROM seccion s
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN nivel n ON n.id_nivel = g.id_nivel
        JOIN matricula m ON m.id_seccion = s.id_seccion AND m.id_anio_escolar = s.id_anio_escolar
        WHERE s.id_anio_escolar = %s
          AND NOT EXISTS (SELECT 1
                          FROM asistencia a
                          JOIN matricula m2 ON m2.id_matricula = a.id_matricula
                          WHERE m2.id_seccion = s.id_seccion AND a.fecha = %s)
        GROUP BY s.id_seccion, g.nombre, s.nombre, n.nombre, g.orden
        ORDER BY g.orden, s.nombre
    """, (id_anio, dia))


def reportes_del_dia(dia) -> int:
    fila = consultar_uno("""
        SELECT COUNT(*) AS total FROM reporte_conducta
        WHERE DATE(fecha_reporte) = %s AND estado = 'REGISTRADO'
    """, (dia,))
    return fila["total"]


# --- Administrador ----------------------------------------------------------------

def totales(id_anio: str) -> dict:
    """Números generales del colegio (cada uno es una subconsulta)."""
    return consultar_uno("""
        SELECT (SELECT COUNT(*) FROM matricula WHERE id_anio_escolar = %s) AS alumnos_matriculados,
               (SELECT COUNT(*) FROM docente) AS docentes,
               (SELECT COUNT(*) FROM cita_psicologia WHERE estado = 'PENDIENTE') AS citas_pendientes,
               (SELECT COUNT(*) FROM reporte_conducta
                 WHERE estado = 'REGISTRADO'
                   AND YEAR(fecha_reporte) = YEAR(CURDATE())
                   AND MONTH(fecha_reporte) = MONTH(CURDATE())) AS reportes_del_mes
    """, (id_anio,))
