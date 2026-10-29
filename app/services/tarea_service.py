"""Reglas de tareas y entregas.

Flujo (propuesta, Flujo 3):
1. El docente publica una tarea con fecha límite.
2. Cada alumno del curso la entrega con un enlace (Drive, PDF...). Puede volver
   a entregar mientras no esté calificada.
3. El docente revisa las entregas y califica (0 a 20) con una observación.

Estado de una tarea para el alumno:
    PENDIENTE   aún no la entregó         (VENCIDA si ya pasó la fecha límite)
    ENTREGADA   la entregó, sin nota
    CALIFICADA  ya tiene nota
"""
from datetime import datetime

from app.database import get_db
from app.errors import ApiError
from app.repositories import perfil_repository, tarea_repository
from app.services import cursos_service, notificacion_service, perfil_service
from app.utils import enlace, entero, fecha_hora, numero, texto

NOTA_MAXIMA = 20
# Regla configurable: ¿se acepta una entrega después de la fecha límite?
# True  → se acepta, pero queda marcada como "fuera_de_plazo".
# False → se rechaza con 409.
ACEPTAR_FUERA_DE_PLAZO = True


# --- Ayudas ---------------------------------------------------------------------

def _buscar_tarea(id_tarea: int) -> dict:
    tarea = tarea_repository.buscar(id_tarea)
    if tarea is None:
        raise ApiError(404, "Tarea no encontrada")
    return tarea


def _estado_entrega(fila: dict, fecha_limite) -> dict:
    """Estado de la entrega de un alumno, a partir de una fila con sus datos de entrega."""
    if fila["id_entrega"] is None:
        vencida = fecha_limite is not None and datetime.now() > fecha_limite
        return {"estado": "VENCIDA" if vencida else "PENDIENTE", "fuera_de_plazo": False}
    fuera = fecha_limite is not None and fila["fecha_envio"] > fecha_limite
    estado = "CALIFICADA" if fila["calificacion"] is not None else "ENTREGADA"
    return {"estado": estado, "fuera_de_plazo": fuera}


# --- Tareas -----------------------------------------------------------------------

def listar(usuario: dict, id_carga: int) -> dict:
    """Tareas de un curso. El docente ve cuántas entregas tiene cada una;
    el alumno ve el estado de SU entrega."""
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_ver_curso(usuario, carga)

    if usuario["rol"] != "ALUMNO":
        return {"curso": carga, "tareas": tarea_repository.listar_para_docente(id_carga)}

    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    tareas = tarea_repository.listar_para_alumno(id_carga, alumno["id_alumno"])
    for tarea in tareas:
        tarea.update(_estado_entrega(tarea, tarea["fecha_entrega"]))
    return {"curso": carga, "tareas": tareas}


def publicar(usuario: dict, id_carga: int, datos: dict) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_docente_del_curso(usuario, carga)

    titulo = texto(datos, "titulo", minimo=3, maximo=150)
    descripcion = texto(datos, "descripcion", minimo=0, maximo=2000, requerido=False) or None
    fecha_entrega = fecha_hora(datos, "fecha_entrega")            # "2026-11-20T23:59"
    bimestre = entero(datos, "bimestre", minimo=1, maximo=4)
    archivo_url = enlace(datos, "archivo_url", maximo=255)         # enunciado (opcional)
    if fecha_entrega <= datetime.now():
        raise ApiError(400, "La fecha límite debe ser futura")

    db = get_db()
    try:
        id_tarea = tarea_repository.crear(id_carga, titulo, descripcion, fecha_entrega,
                                          bimestre, archivo_url)
        notificacion_service.notificar_seccion(
            carga, "TAREA", f"Nueva tarea de {carga['curso']}",
            f"{titulo} · entrega hasta el {fecha_entrega:%d/%m %H:%M}", id_tarea)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Tarea publicada", "tarea": tarea_repository.buscar(id_tarea)}


def eliminar(usuario: dict, id_tarea: int) -> dict:
    tarea = _buscar_tarea(id_tarea)
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(tarea["id_carga_academica"]))
    # Regla: no se borra una tarea que ya tiene entregas (se perderían las notas).
    if tarea_repository.contar_entregas(id_tarea) > 0:
        raise ApiError(409, "La tarea ya tiene entregas y no se puede eliminar")

    db = get_db()
    try:
        tarea_repository.eliminar(id_tarea)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Tarea eliminada"}


# --- Entregas -------------------------------------------------------------------

def entregar(usuario: dict, id_tarea: int, datos: dict) -> tuple[dict, int]:
    """El alumno entrega (o vuelve a entregar). Devuelve (respuesta, 201 nueva / 200 reemplazada)."""
    tarea = _buscar_tarea(id_tarea)
    cursos_service.exigir_ver_curso(usuario, cursos_service.buscar_carga(tarea["id_carga_academica"]))

    archivo_url = enlace(datos, "archivo_url", requerido=True, maximo=255)
    comentario = texto(datos, "comentario", minimo=0, maximo=1000, requerido=False) or None

    fuera_de_plazo = tarea["fecha_entrega"] is not None and datetime.now() > tarea["fecha_entrega"]
    if fuera_de_plazo and not ACEPTAR_FUERA_DE_PLAZO:
        raise ApiError(409, "La fecha límite ya pasó")

    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    anterior = tarea_repository.entrega_de_alumno(id_tarea, alumno["id_alumno"])
    # Regla: una entrega ya calificada no se puede cambiar.
    if anterior is not None and anterior["calificacion"] is not None:
        raise ApiError(409, "Tu entrega ya fue calificada y no se puede cambiar")

    db = get_db()
    try:
        if anterior is None:
            tarea_repository.crear_entrega(id_tarea, alumno["id_alumno"], archivo_url, comentario)
            codigo, mensaje = 201, "Tarea entregada"
        else:
            tarea_repository.actualizar_entrega(anterior["id_entrega"], archivo_url, comentario)
            codigo, mensaje = 200, "Entrega reemplazada"
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": mensaje, "fuera_de_plazo": fuera_de_plazo}, codigo


def entregas(usuario: dict, id_tarea: int) -> dict:
    """Para el docente: cada alumno del curso con su entrega (o sin ella) y un resumen."""
    tarea = _buscar_tarea(id_tarea)
    carga = cursos_service.buscar_carga(tarea["id_carga_academica"])
    cursos_service.exigir_docente_del_curso(usuario, carga)

    alumnos = tarea_repository.entregas_de_tarea(id_tarea, carga["id_seccion"], carga["anio"])
    resumen = {"PENDIENTE": 0, "VENCIDA": 0, "ENTREGADA": 0, "CALIFICADA": 0}
    for alumno in alumnos:
        alumno.update(_estado_entrega(alumno, tarea["fecha_entrega"]))
        resumen[alumno["estado"]] += 1
    return {"tarea": tarea, "resumen": resumen, "alumnos": alumnos}


def calificar(usuario: dict, id_entrega: int, datos: dict) -> dict:
    entrega = tarea_repository.buscar_entrega(id_entrega)
    if entrega is None:
        raise ApiError(404, "Entrega no encontrada")
    tarea = _buscar_tarea(entrega["id_tarea"])
    cursos_service.exigir_docente_del_curso(usuario, cursos_service.buscar_carga(tarea["id_carga_academica"]))

    calificacion = numero(datos, "calificacion", minimo=0, maximo=NOTA_MAXIMA)
    observacion = texto(datos, "observacion", minimo=0, maximo=1000, requerido=False) or None
    # Regla: una entrega se califica una sola vez.
    if entrega["calificacion"] is not None:
        raise ApiError(409, "Esta entrega ya fue calificada")

    db = get_db()
    try:
        tarea_repository.calificar(id_entrega, calificacion, observacion)
        notificacion_service.notificar_alumno(
            entrega["id_alumno"], "CALIFICACION", "Tu tarea fue calificada",
            f"{tarea['titulo']}: {calificacion:g}", tarea["id_tarea"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Entrega calificada", "calificacion": calificacion}
