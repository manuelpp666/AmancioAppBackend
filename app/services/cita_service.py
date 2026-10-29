"""Reglas de las citas de psicología.

Ciclo de vida de una cita:
    PENDIENTE  (el alumno la solicita)
        ↓ el psicólogo la programa (y puede reprogramarla)
    PROGRAMADA
        ↓ el psicólogo la atiende y escribe su observación
    ATENDIDA
Una cita PENDIENTE o PROGRAMADA también puede pasar a CANCELADA.

La observación del psicólogo es reservada: el alumno no la ve.
"""
from datetime import date, datetime

from app.database import get_db
from app.errors import ApiError
from app.repositories import cita_repository, perfil_repository
from app.services import notificacion_service
from app.utils import fecha_hora, texto


def _buscar(id_cita: int) -> dict:
    cita = cita_repository.buscar(id_cita)
    if cita is None:
        raise ApiError(404, "Cita no encontrada")
    return cita


def _exigir_estado(cita: dict, *permitidos: str) -> None:
    """Error 409 si la cita no está en uno de los estados que permiten la acción."""
    if cita["estado"] not in permitidos:
        raise ApiError(409, f"La cita está {cita['estado']} y no permite esta acción")


# --- Alumno ---------------------------------------------------------------------

def solicitar(usuario: dict, datos: dict) -> dict:
    motivo = texto(datos, "motivo", minimo=5, maximo=200)
    disponibilidad = texto(datos, "disponibilidad", minimo=0, maximo=200, requerido=False) or None

    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    if alumno is None:
        raise ApiError(404, "Datos de alumno no encontrados")
    # Regla: solo una cita activa (pendiente o programada) a la vez.
    if cita_repository.contar_activas(alumno["id_alumno"]) > 0:
        raise ApiError(409, "Ya tienes una cita pendiente o programada")

    db = get_db()
    try:
        id_cita = cita_repository.crear(alumno["id_alumno"], motivo, disponibilidad)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Cita solicitada", "id_cita": id_cita}


def mis_citas(usuario: dict) -> list:
    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    if alumno is None:
        raise ApiError(404, "Datos de alumno no encontrados")
    return cita_repository.de_alumno(alumno["id_alumno"])


# --- Psicólogo -----------------------------------------------------------------

def agenda(dia=None) -> dict:
    """Citas del día (por defecto, hoy) y solicitudes que aún no tienen fecha."""
    dia = dia or date.today()
    return {
        "fecha": dia,
        "citas": cita_repository.del_dia(dia),
        "pendientes": cita_repository.pendientes(),
    }


def programar(usuario: dict, id_cita: int, datos: dict) -> dict:
    """Programa una cita pendiente o reprograma una ya programada."""
    fecha_cita = fecha_hora(datos, "fecha_cita")
    if fecha_cita <= datetime.now():
        raise ApiError(400, "La cita debe programarse en una fecha y hora futuras")

    cita = _buscar(id_cita)
    _exigir_estado(cita, "PENDIENTE", "PROGRAMADA")
    psicologo = perfil_repository.psicologo_por_usuario(usuario["id"])
    if psicologo is None:
        raise ApiError(404, "Datos de psicólogo no encontrados")

    db = get_db()
    try:
        cita_repository.programar(id_cita, fecha_cita, psicologo["id_psicologo"])
        accion = "reprogramada" if cita["estado"] == "PROGRAMADA" else "programada"
        notificacion_service.notificar_alumno(
            cita["id_alumno"], "CITA", f"Cita {accion}",
            f"Tu cita con psicología es el {fecha_cita:%d/%m a las %H:%M}", id_cita)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": f"Cita {accion}", "fecha_cita": fecha_cita}


def completar(id_cita: int, datos: dict) -> dict:
    observacion = texto(datos, "observacion", minimo=3, maximo=2000)
    cita = _buscar(id_cita)
    _exigir_estado(cita, "PROGRAMADA")

    db = get_db()
    try:
        cita_repository.completar(id_cita, observacion)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Cita atendida"}


def cancelar(id_cita: int, datos: dict) -> dict:
    motivo = texto(datos, "motivo", minimo=5, maximo=300)
    cita = _buscar(id_cita)
    _exigir_estado(cita, "PENDIENTE", "PROGRAMADA")

    db = get_db()
    try:
        cita_repository.cancelar(id_cita, motivo)
        notificacion_service.notificar_alumno(cita["id_alumno"], "CITA", "Cita cancelada", motivo, id_cita)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Cita cancelada"}


def historial_de_alumno(id_alumno: int) -> dict:
    """Para el psicólogo: todas las citas de un alumno, con sus observaciones."""
    alumno = perfil_repository.alumno_por_id(id_alumno)
    if alumno is None:
        raise ApiError(404, "Alumno no encontrado")
    citas = cita_repository.historial_completo(id_alumno)
    atendidas = sum(1 for c in citas if c["estado"] == "ATENDIDA")
    return {"alumno": f"{alumno['nombres']} {alumno['apellidos']}",
            "total": len(citas), "atendidas": atendidas, "citas": citas}
