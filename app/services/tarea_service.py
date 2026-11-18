"""Reglas de tareas y entregas.

Flujo (propuesta, Flujo 3):
1. El docente publica una tarea con fecha límite. Puede adjuntar el enunciado como
   enlace y/o como archivo (PDF, Word, imagen...).
2. Cada alumno del curso la entrega con un ARCHIVO (PDF, Word, Excel, PowerPoint,
   imagen...) y/o un ENLACE (Drive...): al menos uno de los dos. Puede volver a
   entregar mientras no esté calificada (la nueva entrega reemplaza a la anterior).
3. El docente revisa las entregas y califica (0 a 20) con una observación.

Estado de una tarea para el alumno:
    PENDIENTE   aún no la entregó         (VENCIDA si ya pasó la fecha límite)
    ENTREGADA   la entregó, sin nota
    CALIFICADA  ya tiene nota

En las respuestas, cada tarea trae "adjunto" (archivo del enunciado) y cada entrega
trae "archivo" (archivo del alumno): {"nombre", "tipo", "tamano", "url"} o null.
Los tipos de archivo permitidos están en app/services/archivo_service.py.
"""
from datetime import datetime

from app.database import get_db
from app.errors import ApiError
from app.repositories import perfil_repository, tarea_repository
from app.services import archivo_service, cursos_service, notificacion_service
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


def _con_archivos(fila: dict, con_entrega: bool = False) -> dict:
    """Junta las columnas de los archivos en objetos: "adjunto" (enunciado) y,
    si la fila trae la entrega de un alumno, "archivo" (lo que subió)."""
    if "adjunto_id" in fila:
        archivo_service.anidar(fila, "adjunto_", "adjunto")
        fila.pop("id_archivo", None)
    if con_entrega:
        archivo_service.anidar(fila, "archivo_", "archivo")
    return fila


def _estado_entrega(fila: dict, fecha_limite) -> dict:
    """Estado de la entrega de un alumno, a partir de una fila con sus datos de entrega."""
    id_entrega = fila.get("id_entrega")
    if id_entrega is None:
        vencida = fecha_limite is not None and datetime.now() > fecha_limite
        return {"estado": "VENCIDA" if vencida else "PENDIENTE", "fuera_de_plazo": False}
    fecha_envio = fila.get("fecha_envio")
    fuera = bool(fecha_limite is not None and fecha_envio is not None and fecha_envio > fecha_limite)
    estado = "CALIFICADA" if fila.get("calificacion") is not None else "ENTREGADA"
    return {"estado": estado, "fuera_de_plazo": fuera}


# --- Tareas -----------------------------------------------------------------------

def listar(usuario: dict, id_carga: int) -> dict:
    """Tareas de un curso. El docente ve cuántas entregas tiene cada una;
    el alumno ve el estado de SU entrega."""
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_ver_curso(usuario, carga)

    if usuario["rol"] != "ALUMNO":
        tareas = [_con_archivos(t) for t in tarea_repository.listar_para_docente(id_carga)]
        return {"curso": carga, "tareas": tareas}

    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    tareas = tarea_repository.listar_para_alumno(id_carga, alumno["id_alumno"])
    for tarea in tareas:
        tarea.update(_estado_entrega(tarea, tarea["fecha_entrega"]))
        _con_archivos(tarea, con_entrega=True)
    return {"curso": carga, "tareas": tareas}


def obtener(usuario: dict, id_tarea: int) -> dict:
    """Detalle de una tarea específica con el estado de entrega del alumno si corresponde."""
    if usuario["rol"] == "ALUMNO":
        alumno = perfil_repository.alumno_por_usuario(usuario["id"])
        if alumno is None:
            raise ApiError(404, "Datos de alumno no encontrados")
        tarea = tarea_repository.buscar_para_alumno(id_tarea, alumno["id_alumno"])
        if tarea is None:
            raise ApiError(404, "Tarea no encontrada")
        carga = cursos_service.buscar_carga(tarea["id_carga_academica"])
        cursos_service.exigir_ver_curso(usuario, carga)
        tarea.update(_estado_entrega(tarea, tarea["fecha_entrega"]))
        _con_archivos(tarea, con_entrega=True)
    else:
        tarea = _buscar_tarea(id_tarea)
        carga = cursos_service.buscar_carga(tarea["id_carga_academica"])
        cursos_service.exigir_ver_curso(usuario, carga)
        _con_archivos(tarea)

    return {"tarea": tarea, "curso": carga}


def publicar(usuario: dict, id_carga: int, datos: dict, archivo=None) -> dict:
    """El docente publica una tarea. `archivo` (opcional) es el enunciado subido."""
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
    guardado = None
    try:
        if archivo is not None:
            guardado = archivo_service.guardar(archivo, usuario["id"])
        id_tarea = tarea_repository.crear(id_carga, titulo, descripcion, fecha_entrega, bimestre,
                                          archivo_url, guardado and guardado["id_archivo"])
        notificacion_service.notificar_seccion(
            carga, "TAREA", f"Nueva tarea de {carga['curso']}",
            f"{titulo} · entrega hasta el {fecha_entrega:%d/%m %H:%M}", id_tarea)
        db.commit()
    except Exception:
        db.rollback()
        archivo_service.borrar_del_disco(guardado and guardado["ruta"])
        raise
    return {"message": "Tarea publicada", "tarea": _con_archivos(tarea_repository.buscar(id_tarea))}


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
    archivo_service.eliminar(tarea["id_archivo"])       # el enunciado subido, si había
    return {"message": "Tarea eliminada"}


# --- Entregas -------------------------------------------------------------------

def entregar(usuario: dict, id_tarea: int, datos: dict, archivo=None) -> tuple[dict, int]:
    """El alumno entrega (o vuelve a entregar) con un archivo y/o un enlace.
    Devuelve (respuesta, 201 nueva / 200 reemplazada)."""
    tarea = _buscar_tarea(id_tarea)
    cursos_service.exigir_ver_curso(usuario, cursos_service.buscar_carga(tarea["id_carga_academica"]))

    archivo_url = enlace(datos, "archivo_url", maximo=255)
    comentario = texto(datos, "comentario", minimo=0, maximo=1000, requerido=False) or None
    if archivo is None and not archivo_url:
        raise ApiError(400, "Sube un archivo o pega el enlace de tu trabajo")

    fuera_de_plazo = tarea["fecha_entrega"] is not None and datetime.now() > tarea["fecha_entrega"]
    if fuera_de_plazo and not ACEPTAR_FUERA_DE_PLAZO:
        raise ApiError(409, "La fecha límite ya pasó")

    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    anterior = tarea_repository.entrega_de_alumno(id_tarea, alumno["id_alumno"])
    # Regla: una entrega ya calificada no se puede cambiar.
    if anterior is not None and anterior["calificacion"] is not None:
        raise ApiError(409, "Tu entrega ya fue calificada y no se puede cambiar")

    db = get_db()
    guardado = None
    try:
        if archivo is not None:
            guardado = archivo_service.guardar(archivo, usuario["id"])
        id_archivo = guardado and guardado["id_archivo"]
        if anterior is None:
            tarea_repository.crear_entrega(id_tarea, alumno["id_alumno"], archivo_url, comentario, id_archivo)
            codigo, mensaje = 201, "Tarea entregada"
        else:
            tarea_repository.actualizar_entrega(anterior["id_entrega"], archivo_url, comentario, id_archivo)
            codigo, mensaje = 200, "Entrega reemplazada"
        db.commit()
    except Exception:
        db.rollback()
        archivo_service.borrar_del_disco(guardado and guardado["ruta"])
        raise
    # La entrega nueva reemplaza a la anterior: su archivo ya no se usa.
    if anterior is not None:
        archivo_service.eliminar(anterior["id_archivo"])
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
        _con_archivos(alumno, con_entrega=True)
        resumen[alumno["estado"]] += 1
    return {"tarea": _con_archivos(tarea), "resumen": resumen, "alumnos": alumnos}


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
