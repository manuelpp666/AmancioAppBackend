"""Consultas SQL de tareas (`tarea`) y entregas (`entrega_tarea`).

tarea.fecha_entrega          = fecha límite para entregar
tarea.archivo_adjunto_url    = enlace al enunciado (opcional)
tarea.id_archivo             = archivo subido como enunciado (opcional, tabla `archivo`)
entrega_tarea.archivo_url    = enlace a lo que entregó el alumno (Drive...)       ┐ al menos
entrega_tarea.id_archivo     = archivo que subió el alumno (PDF, Word, imagen...)  ┘ uno de los dos
entrega_tarea.calificacion   = NULL mientras el docente no la califique

Los datos del archivo salen con un prefijo (adjunto_* para el enunciado y archivo_* para
la entrega); el service los junta en un solo objeto con archivo_service.anidar().
"""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar

_COLUMNAS_TAREA = """t.id_tarea, t.id_carga_academica, t.titulo, t.descripcion, t.fecha_publicacion,
                     t.fecha_entrega, t.archivo_adjunto_url, t.id_archivo, t.bimestre,
                     adj.id_archivo AS adjunto_id, adj.nombre_original AS adjunto_nombre,
                     adj.tipo_mime AS adjunto_tipo, adj.tamano_bytes AS adjunto_tamano"""
_UNIR_ADJUNTO = "LEFT JOIN archivo adj ON adj.id_archivo = t.id_archivo"

# Entrega del alumno (e) con su archivo (arc).
_COLUMNAS_ENTREGA = """e.id_entrega, e.archivo_url, e.fecha_envio, e.calificacion, e.retroalimentacion_docente,
                       arc.id_archivo AS archivo_id, arc.nombre_original AS archivo_nombre,
                       arc.tipo_mime AS archivo_tipo, arc.tamano_bytes AS archivo_tamano"""
_UNIR_ARCHIVO_ENTREGA = "LEFT JOIN archivo arc ON arc.id_archivo = e.id_archivo"


# --- Tareas ---------------------------------------------------------------------

def buscar(id_tarea: int):
    return consultar_uno(f"""
        SELECT {_COLUMNAS_TAREA} FROM tarea t {_UNIR_ADJUNTO}
        WHERE t.id_tarea = %s
    """, (id_tarea,))


def buscar_para_alumno(id_tarea: int, id_alumno: int):
    """Tarea con la entrega de ESE alumno (NULL si no entregó)."""
    return consultar_uno(f"""
        SELECT {_COLUMNAS_TAREA}, {_COLUMNAS_ENTREGA}
        FROM tarea t
        {_UNIR_ADJUNTO}
        LEFT JOIN entrega_tarea e ON e.id_tarea = t.id_tarea AND e.id_alumno = %s
        {_UNIR_ARCHIVO_ENTREGA}
        WHERE t.id_tarea = %s
    """, (id_alumno, id_tarea))


def listar_para_docente(id_carga: int) -> list:
    """Tareas del curso con cuántas entregas tiene cada una y cuántas ya calificó.
    COUNT(calificacion) solo cuenta las que NO son NULL."""
    return consultar_todos(f"""
        SELECT {_COLUMNAS_TAREA},
               (SELECT COUNT(*) FROM entrega_tarea e WHERE e.id_tarea = t.id_tarea) AS entregas,
               (SELECT COUNT(e.calificacion) FROM entrega_tarea e WHERE e.id_tarea = t.id_tarea) AS calificadas
        FROM tarea t
        {_UNIR_ADJUNTO}
        WHERE t.id_carga_academica = %s
        ORDER BY t.fecha_entrega
    """, (id_carga,))


def listar_para_alumno(id_carga: int, id_alumno: int) -> list:
    """Tareas del curso con la entrega de ESE alumno (NULL si no entregó)."""
    return consultar_todos(f"""
        SELECT {_COLUMNAS_TAREA}, {_COLUMNAS_ENTREGA}
        FROM tarea t
        {_UNIR_ADJUNTO}
        LEFT JOIN entrega_tarea e ON e.id_tarea = t.id_tarea AND e.id_alumno = %s
        {_UNIR_ARCHIVO_ENTREGA}
        WHERE t.id_carga_academica = %s
        ORDER BY t.fecha_entrega
    """, (id_alumno, id_carga))


def crear(id_carga: int, titulo: str, descripcion, fecha_entrega, bimestre: int, archivo_url,
          id_archivo=None) -> int:
    return insertar("""
        INSERT INTO tarea (id_carga_academica, titulo, descripcion, fecha_entrega, bimestre,
                           archivo_adjunto_url, id_archivo, estado, tipo_evaluacion, peso)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVO', 'TAREA', 0)
    """, (id_carga, titulo, descripcion, fecha_entrega, bimestre, archivo_url, id_archivo))


def contar_entregas(id_tarea: int) -> int:
    fila = consultar_uno("SELECT COUNT(*) AS total FROM entrega_tarea WHERE id_tarea = %s", (id_tarea,))
    return fila["total"]


def eliminar(id_tarea: int) -> int:
    return ejecutar("DELETE FROM tarea WHERE id_tarea = %s", (id_tarea,))


# --- Entregas -------------------------------------------------------------------

def buscar_entrega(id_entrega: int):
    return consultar_uno("""
        SELECT id_entrega, id_tarea, id_alumno, archivo_url, id_archivo, fecha_envio, calificacion
        FROM entrega_tarea
        WHERE id_entrega = %s
    """, (id_entrega,))


def entrega_de_alumno(id_tarea: int, id_alumno: int):
    """La entrega de un alumno para una tarea, o None si aún no entregó."""
    return consultar_uno("""
        SELECT id_entrega, id_archivo, calificacion
        FROM entrega_tarea
        WHERE id_tarea = %s AND id_alumno = %s
    """, (id_tarea, id_alumno))


def crear_entrega(id_tarea: int, id_alumno: int, archivo_url, comentario, id_archivo=None) -> int:
    return insertar("""
        INSERT INTO entrega_tarea (id_tarea, id_alumno, archivo_url, id_archivo, comentario_alumno, fecha_envio)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (id_tarea, id_alumno, archivo_url, id_archivo, comentario))


def actualizar_entrega(id_entrega: int, archivo_url, comentario, id_archivo=None) -> int:
    """Vuelve a entregar: reemplaza el enlace, el archivo y el comentario, con la fecha de ahora."""
    return ejecutar("""
        UPDATE entrega_tarea
        SET archivo_url = %s, id_archivo = %s, comentario_alumno = %s, fecha_envio = NOW()
        WHERE id_entrega = %s
    """, (archivo_url, id_archivo, comentario, id_entrega))


def entregas_de_tarea(id_tarea: int, id_seccion: int, id_anio: str) -> list:
    """Todos los alumnos de la sección con su entrega (NULL si no entregaron)."""
    return consultar_todos(f"""
        SELECT a.id_alumno, a.apellidos, a.nombres, e.comentario_alumno, {_COLUMNAS_ENTREGA}
        FROM matricula m
        JOIN alumno a ON a.id_alumno = m.id_alumno
        LEFT JOIN entrega_tarea e ON e.id_alumno = a.id_alumno AND e.id_tarea = %s
        {_UNIR_ARCHIVO_ENTREGA}
        WHERE m.id_seccion = %s AND m.id_anio_escolar = %s
        ORDER BY a.apellidos, a.nombres
    """, (id_tarea, id_seccion, id_anio))


def calificar(id_entrega: int, calificacion: float, observacion) -> int:
    return ejecutar("""
        UPDATE entrega_tarea
        SET calificacion = %s, retroalimentacion_docente = %s
        WHERE id_entrega = %s
    """, (calificacion, observacion, id_entrega))
