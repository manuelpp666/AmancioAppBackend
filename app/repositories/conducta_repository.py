"""Consultas SQL de conducta: catálogo de faltas y reportes."""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar


def faltas() -> list:
    """Catálogo de faltas con su tipo y los puntos que descuentan."""
    return consultar_todos("""
        SELECT nc.id_nivel_conducta AS id_falta, nc.nombre, t.nombre AS tipo,
               nc.puntos, nc.descripcion
        FROM nivel_conducta nc
        JOIN tipo_falta t ON t.id_tipo_falta = nc.id_tipo_falta
        ORDER BY nc.puntos, nc.nombre
    """)


def falta_por_id(id_falta: int):
    return consultar_uno("""
        SELECT id_nivel_conducta AS id_falta, nombre, puntos
        FROM nivel_conducta
        WHERE id_nivel_conducta = %s
    """, (id_falta,))


def crear_reporte(id_alumno: int, id_falta: int, registrado_por: int,
                  fecha_reporte, descripcion: str, evidencia_url) -> int:
    return insertar("""
        INSERT INTO reporte_conducta
            (id_alumno, id_nivel_conducta, registrado_por, fecha_reporte,
             descripcion_suceso, evidencia_url, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'REGISTRADO')
    """, (id_alumno, id_falta, registrado_por, fecha_reporte, descripcion, evidencia_url))


def buscar_reporte(id_reporte: int):
    return consultar_uno("""
        SELECT id_reporte, id_alumno, estado
        FROM reporte_conducta
        WHERE id_reporte = %s
    """, (id_reporte,))


def anular_reporte(id_reporte: int, motivo: str, id_usuario: int) -> int:
    """Marca el reporte como ANULADO (no se borra): guarda el motivo, quién y cuándo."""
    return ejecutar("""
        UPDATE reporte_conducta
        SET estado = 'ANULADO', motivo_anulacion = %s, anulado_por = %s, fecha_anulacion = NOW()
        WHERE id_reporte = %s AND estado = 'REGISTRADO'
    """, (motivo, id_usuario, id_reporte))


def reportes_de_alumno(id_alumno: int, desde, hasta) -> list:
    """Reportes de un alumno entre dos fechas (el año escolar), del más reciente al más antiguo."""
    return consultar_todos("""
        SELECT r.id_reporte, r.fecha_reporte, nc.nombre AS falta, t.nombre AS tipo,
               nc.puntos, r.descripcion_suceso, r.evidencia_url, r.estado,
               r.motivo_anulacion, r.fecha_anulacion
        FROM reporte_conducta r
        JOIN nivel_conducta nc ON nc.id_nivel_conducta = r.id_nivel_conducta
        JOIN tipo_falta t ON t.id_tipo_falta = nc.id_tipo_falta
        WHERE r.id_alumno = %s AND DATE(r.fecha_reporte) BETWEEN %s AND %s
        ORDER BY r.fecha_reporte DESC
    """, (id_alumno, desde, hasta))


def puntos_por_bimestre(id_alumno: int, id_anio: str) -> list:
    """Puntos descontados en cada bimestre del año (solo reportes vigentes).

    LEFT JOIN: aunque un bimestre no tenga reportes, sale con 0 puntos.
    """
    return consultar_todos("""
        SELECT b.numero AS bimestre, COALESCE(SUM(nc.puntos), 0) AS puntos
        FROM bimestre b
        LEFT JOIN reporte_conducta r
               ON r.id_alumno = %s
              AND r.estado = 'REGISTRADO'
              AND DATE(r.fecha_reporte) BETWEEN b.fecha_inicio AND b.fecha_fin
        LEFT JOIN nivel_conducta nc ON nc.id_nivel_conducta = r.id_nivel_conducta
        WHERE b.id_anio_escolar = %s
        GROUP BY b.numero
        ORDER BY b.numero
    """, (id_alumno, id_anio))
