"""Consultas SQL de notas.

Tablas que se usan:
    nota             una nota de una evaluación (ej. "Práctica 1": 15.5)
                     tipo_nota = nombre de la evaluación
    resumen_nota     la libreta: el promedio de cada bimestre ya cerrado, en
                     columnas nota_bimestre1 ... nota_bimestre4, y el promedio final
    cierre_bimestre  qué bimestres ya cerró el docente en cada curso
"""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar


# --- Notas de las evaluaciones ----------------------------------------------------

def guardar_nota(id_matricula: int, id_curso: int, bimestre: int, evaluacion: str, valor: float) -> int:
    """Crea la nota, o la actualiza si ese alumno ya tenía nota en esa evaluación.

    ON DUPLICATE KEY UPDATE funciona gracias a la clave única
    (id_matricula, id_curso, bimestre, tipo_nota) de la tabla `nota`.
    """
    return insertar("""
        INSERT INTO nota (id_matricula, id_curso, bimestre, tipo_nota, valor)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE valor = VALUES(valor), fecha_registro = NOW()
    """, (id_matricula, id_curso, bimestre, evaluacion, valor))


def notas_del_curso(id_curso: int, id_seccion: int, id_anio: str, bimestre: int) -> list:
    """Todas las notas de un curso en un bimestre, una fila por alumno y evaluación.

    LEFT JOIN: los alumnos sin notas también salen (con evaluacion y valor en NULL).
    """
    return consultar_todos("""
        SELECT a.id_alumno, a.apellidos, a.nombres, n.tipo_nota AS evaluacion, n.valor
        FROM matricula m
        JOIN alumno a ON a.id_alumno = m.id_alumno
        LEFT JOIN nota n ON n.id_matricula = m.id_matricula
                        AND n.id_curso = %s AND n.bimestre = %s
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s
        ORDER BY a.apellidos, a.nombres, n.fecha_registro, n.id_nota
    """, (id_curso, bimestre, id_seccion, id_anio))


def promedios_del_bimestre(id_curso: int, id_seccion: int, id_anio: str, bimestre: int) -> list:
    """Promedio de cada alumno en un bimestre (AVG de sus evaluaciones).
    Si un alumno no tiene notas, sale con promedio NULL y 0 evaluaciones."""
    return consultar_todos("""
        SELECT m.id_matricula, a.nombres, a.apellidos,
               ROUND(AVG(n.valor), 2) AS promedio, COUNT(n.id_nota) AS evaluaciones
        FROM matricula m
        JOIN alumno a ON a.id_alumno = m.id_alumno
        LEFT JOIN nota n ON n.id_matricula = m.id_matricula
                        AND n.id_curso = %s AND n.bimestre = %s
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s
        GROUP BY m.id_matricula, a.nombres, a.apellidos
        ORDER BY a.apellidos, a.nombres
    """, (id_curso, bimestre, id_seccion, id_anio))


def notas_de_alumno(id_matricula: int, bimestre: int) -> list:
    """Notas de un alumno en un bimestre, en todos sus cursos."""
    return consultar_todos("""
        SELECT n.id_curso, n.tipo_nota AS evaluacion, n.valor
        FROM nota n
        WHERE n.id_matricula = %s AND n.bimestre = %s
        ORDER BY n.fecha_registro, n.id_nota
    """, (id_matricula, bimestre))


# --- Cierre de bimestre ------------------------------------------------------------

def bimestres_cerrados(id_carga: int) -> list:
    """Números de los bimestres ya cerrados en un curso, ej. [1, 2]."""
    filas = consultar_todos("""
        SELECT bimestre FROM cierre_bimestre
        WHERE id_carga_academica = %s
        ORDER BY bimestre
    """, (id_carga,))
    return [fila["bimestre"] for fila in filas]


def registrar_cierre(id_carga: int, bimestre: int, id_usuario: int) -> int:
    return insertar("""
        INSERT INTO cierre_bimestre (id_carga_academica, bimestre, cerrado_por)
        VALUES (%s, %s, %s)
    """, (id_carga, bimestre, id_usuario))


# --- Libreta (resumen_nota) ---------------------------------------------------------

def guardar_promedio_bimestre(id_matricula: int, id_curso: int, bimestre: int, promedio: float) -> int:
    """Pasa el promedio de un bimestre a la libreta (crea la fila si no existe).

    La columna depende del bimestre (nota_bimestre1 ... nota_bimestre4). Su nombre
    no puede ir como %s, así que se arma con el número, que el service ya validó
    que sea 1, 2, 3 o 4.
    """
    columna = f"nota_bimestre{int(bimestre)}"
    return insertar(f"""
        INSERT INTO resumen_nota (id_matricula, id_curso, {columna}, estado_curso)
        VALUES (%s, %s, %s, 'EN CURSO')
        ON DUPLICATE KEY UPDATE {columna} = VALUES({columna})
    """, (id_matricula, id_curso, promedio))


def resumen(id_matricula: int, id_curso: int):
    return consultar_uno("""
        SELECT nota_bimestre1, nota_bimestre2, nota_bimestre3, nota_bimestre4
        FROM resumen_nota
        WHERE id_matricula = %s AND id_curso = %s
    """, (id_matricula, id_curso))


def actualizar_promedio_final(id_matricula: int, id_curso: int, promedio_final: float,
                              estado: str) -> int:
    return ejecutar("""
        UPDATE resumen_nota
        SET promedio_final = %s, estado_curso = %s
        WHERE id_matricula = %s AND id_curso = %s
    """, (promedio_final, estado, id_matricula, id_curso))


def libreta(id_matricula: int) -> list:
    """La libreta del alumno: una fila por curso con los promedios de los bimestres cerrados."""
    return consultar_todos("""
        SELECT c.id_curso, c.nombre AS curso, r.nota_bimestre1, r.nota_bimestre2,
               r.nota_bimestre3, r.nota_bimestre4, r.promedio_final, r.estado_curso
        FROM resumen_nota r
        JOIN curso c ON c.id_curso = r.id_curso
        WHERE r.id_matricula = %s
        ORDER BY c.nombre
    """, (id_matricula,))
