"""Consultas SQL de la tabla `cita_psicologia`.

estado: PENDIENTE (solicitada) → PROGRAMADA → ATENDIDA, o CANCELADA.
"""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar


def crear(id_alumno: int, motivo: str, disponibilidad) -> int:
    return insertar("""
        INSERT INTO cita_psicologia (id_alumno, motivo, disponibilidad, estado)
        VALUES (%s, %s, %s, 'PENDIENTE')
    """, (id_alumno, motivo, disponibilidad))


def buscar(id_cita: int):
    return consultar_uno("""
        SELECT id_cita, id_alumno, id_psicologo, motivo, fecha_cita, estado
        FROM cita_psicologia
        WHERE id_cita = %s
    """, (id_cita,))


def contar_activas(id_alumno: int) -> int:
    """Cuántas citas tiene el alumno sin terminar (PENDIENTE o PROGRAMADA)."""
    fila = consultar_uno("""
        SELECT COUNT(*) AS total
        FROM cita_psicologia
        WHERE id_alumno = %s AND estado IN ('PENDIENTE', 'PROGRAMADA')
    """, (id_alumno,))
    return fila["total"]


def de_alumno(id_alumno: int) -> list:
    """Historial del alumno. NO incluye la observación del psicólogo (es reservada)."""
    return consultar_todos("""
        SELECT id_cita, motivo, disponibilidad, fecha_solicitud, fecha_cita, estado,
               motivo_cancelacion
        FROM cita_psicologia
        WHERE id_alumno = %s
        ORDER BY fecha_solicitud DESC
    """, (id_alumno,))


# Datos de la cita con el nombre del alumno, para el psicólogo.
_SELECT_AGENDA = """
    SELECT c.id_cita, c.id_alumno, CONCAT(a.nombres, ' ', a.apellidos) AS alumno,
           c.motivo, c.disponibilidad, c.fecha_solicitud, c.fecha_cita, c.estado, c.observacion
    FROM cita_psicologia c
    JOIN alumno a ON a.id_alumno = c.id_alumno
"""


def pendientes() -> list:
    """Solicitudes que aún no tienen fecha, la más antigua primero."""
    return consultar_todos(_SELECT_AGENDA + """
        WHERE c.estado = 'PENDIENTE'
        ORDER BY c.fecha_solicitud
    """)


def del_dia(dia) -> list:
    """Citas programadas o atendidas en una fecha, por hora."""
    return consultar_todos(_SELECT_AGENDA + """
        WHERE DATE(c.fecha_cita) = %s AND c.estado IN ('PROGRAMADA', 'ATENDIDA')
        ORDER BY c.fecha_cita
    """, (dia,))


def programar(id_cita: int, fecha_cita, id_psicologo: int) -> int:
    return ejecutar("""
        UPDATE cita_psicologia
        SET fecha_cita = %s, id_psicologo = %s, estado = 'PROGRAMADA'
        WHERE id_cita = %s
    """, (fecha_cita, id_psicologo, id_cita))


def completar(id_cita: int, observacion: str) -> int:
    return ejecutar("""
        UPDATE cita_psicologia
        SET estado = 'ATENDIDA', observacion = %s
        WHERE id_cita = %s
    """, (observacion, id_cita))


def cancelar(id_cita: int, motivo: str) -> int:
    return ejecutar("""
        UPDATE cita_psicologia
        SET estado = 'CANCELADA', motivo_cancelacion = %s
        WHERE id_cita = %s
    """, (motivo, id_cita))
