"""Reglas de conducta.

- El auxiliar registra reportes (partes) eligiendo una falta del catálogo.
- Un reporte no se borra: se ANULA con un motivo (queda quién y cuándo).
- Nota de conducta = 20 − puntos de los reportes vigentes del bimestre
  (mínimo 0). Se reinicia en cada bimestre y no se guarda: se calcula.
"""
from datetime import date, datetime

from app.database import get_db
from app.errors import ApiError
from app.repositories import academico_repository, conducta_repository, perfil_repository
from app.services import academico_service, notificacion_service
from app.utils import enlace, entero, fecha, texto

NOTA_MAXIMA = 20
ROLES_PERSONAL = ("AUXILIAR", "PSICOLOGO", "DOCENTE", "ADMIN")


def catalogo() -> list:
    return conducta_repository.faltas()


def registrar_reporte(usuario: dict, datos: dict) -> dict:
    id_alumno = entero(datos, "id_alumno", minimo=1, maximo=2_000_000_000)
    id_falta = entero(datos, "id_falta", minimo=1, maximo=2_000_000_000)
    descripcion = texto(datos, "descripcion", minimo=5, maximo=1000)
    evidencia_url = enlace(datos, "evidencia_url")              # foto opcional
    dia = fecha(datos, "fecha", requerido=False) or date.today()
    if dia > date.today():
        raise ApiError(400, "La fecha del reporte no puede ser futura")

    if perfil_repository.alumno_por_id(id_alumno) is None:
        raise ApiError(404, "Alumno no encontrado")
    falta = conducta_repository.falta_por_id(id_falta)
    if falta is None:
        raise ApiError(404, "Falta no encontrada en el catálogo")

    # Se guarda la fecha indicada con la hora actual.
    fecha_reporte = datetime.combine(dia, datetime.now().time()).replace(microsecond=0)

    db = get_db()
    try:
        id_reporte = conducta_repository.crear_reporte(id_alumno, id_falta, usuario["id"],
                                                       fecha_reporte, descripcion, evidencia_url)
        notificacion_service.notificar_alumno(
            id_alumno, "CONDUCTA", "Nuevo reporte de conducta",
            f"{falta['nombre']} (−{falta['puntos']} puntos)", id_reporte)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Reporte registrado", "id_reporte": id_reporte}


def anular_reporte(usuario: dict, id_reporte: int, datos: dict) -> dict:
    motivo = texto(datos, "motivo", minimo=5, maximo=300)

    reporte = conducta_repository.buscar_reporte(id_reporte)
    if reporte is None:
        raise ApiError(404, "Reporte no encontrado")
    if reporte["estado"] == "ANULADO":
        raise ApiError(409, "El reporte ya estaba anulado")

    db = get_db()
    try:
        conducta_repository.anular_reporte(id_reporte, motivo, usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Reporte anulado"}


def estado_conducta(usuario: dict, id_alumno: int) -> dict:
    alumno = perfil_repository.alumno_por_id(id_alumno)
    if alumno is None:
        raise ApiError(404, "Alumno no encontrado")

    # Un alumno solo puede ver su propia conducta; el personal, la de cualquiera.
    if usuario["rol"] == "ALUMNO":
        if alumno["id_usuario"] != usuario["id"]:
            raise ApiError(403, "No puedes ver la conducta de otro alumno")
    elif usuario["rol"] not in ROLES_PERSONAL:
        raise ApiError(403, "No tienes permisos para ver la conducta")

    anio = academico_service.anio_activo()

    # Nota de cada bimestre: 20 menos los puntos descontados (mínimo 0).
    notas = []
    for fila in conducta_repository.puntos_por_bimestre(id_alumno, anio["id_anio_escolar"]):
        puntos = int(fila["puntos"])
        notas.append({"bimestre": fila["bimestre"], "puntos": puntos,
                      "nota": max(0, NOTA_MAXIMA - puntos)})

    actual = academico_repository.bimestre_de_fecha(anio["id_anio_escolar"], date.today())
    numero_actual = actual["numero"] if actual else None
    nota_actual = next((n["nota"] for n in notas if n["bimestre"] == numero_actual), NOTA_MAXIMA)

    hasta = anio["fecha_fin"] or date.today()
    return {
        "alumno": {"id_alumno": alumno["id_alumno"], "nombres": alumno["nombres"],
                   "apellidos": alumno["apellidos"]},
        "anio": anio["id_anio_escolar"],
        "bimestre_actual": numero_actual,
        "nota_actual": nota_actual,
        "notas_por_bimestre": notas,
        "reportes": conducta_repository.reportes_de_alumno(id_alumno, anio["fecha_inicio"], hasta),
    }
