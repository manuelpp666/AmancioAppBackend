"""Panel de inicio: la primera pantalla de la app, distinta para cada rol.

Junta en una sola respuesta lo más importante del día, reutilizando lo que ya
hacen los otros módulos (horario, asistencia, conducta, citas...):

    ALUMNO     clases de hoy, próximas tareas sin entregar, últimas notas,
               resumen de asistencia, nota de conducta, cita activa, próximas clases virtuales
    DOCENTE    clases de hoy, entregas por calificar, próximas clases virtuales
    AUXILIAR   secciones sin asistencia hoy, reportes de conducta de hoy
    PSICOLOGO  citas de hoy y solicitudes pendientes
    ADMIN      totales del colegio

Todos reciben además cuántos mensajes y notificaciones tienen sin leer.
"""
from datetime import date

from app.errors import ApiError
from app.repositories import (cita_repository, inicio_repository, mensaje_repository,
                              notificacion_repository, perfil_repository)
from app.services import (academico_service, asistencia_service, conducta_service,
                          cursos_service, horario_service)


def _clases_de_hoy(usuario: dict) -> list:
    """Los bloques del horario de hoy (lunes a viernes; el fin de semana, ninguno)."""
    dia = date.today().isoweekday()          # 1 = lunes ... 7 = domingo
    if dia > 5:
        return []
    return horario_service.mi_horario(usuario)["dias"][dia - 1]["bloques"]


def panel(usuario: dict) -> dict:
    anio = academico_service.anio_activo()["id_anio_escolar"]
    rol = usuario["rol"]
    ficha = perfil_repository.ficha(rol, usuario["id"])
    if ficha is None:
        raise ApiError(404, f"Datos de {rol.lower()} no encontrados")

    respuesta = {
        "rol": rol,
        "nombre": f"{ficha['nombres']} {ficha['apellidos']}",
        "fecha": date.today(),
        "mensajes_no_leidos": mensaje_repository.no_leidos_total(usuario["id"]),
        "notificaciones_no_leidas": notificacion_repository.contar_no_leidas(usuario["id"]),
    }

    if rol == "ALUMNO":
        respuesta.update(_panel_alumno(usuario, ficha, anio))
    elif rol == "DOCENTE":
        respuesta.update({
            "clases_de_hoy": _clases_de_hoy(usuario),
            "entregas_por_calificar": inicio_repository.entregas_por_calificar(ficha["id_docente"], anio),
            "proximas_clases_virtuales": inicio_repository.proximas_clases_de_docente(ficha["id_docente"], anio),
        })
    elif rol == "AUXILIAR":
        respuesta.update({
            "secciones_sin_asistencia_hoy": inicio_repository.secciones_sin_asistencia(anio, date.today()),
            "reportes_de_hoy": inicio_repository.reportes_del_dia(date.today()),
        })
    elif rol == "PSICOLOGO":
        pendientes = cita_repository.pendientes()
        respuesta.update({
            "citas_de_hoy": cita_repository.del_dia(date.today()),
            "solicitudes_pendientes": len(pendientes),
            "solicitudes": pendientes[:5],
        })
    else:   # ADMIN
        respuesta["totales"] = inicio_repository.totales(anio)
    return respuesta


def _panel_alumno(usuario: dict, ficha: dict, anio: str) -> dict:
    matricula = cursos_service.matricula_actual(usuario["id"])
    if matricula is None or matricula["id_seccion"] is None:
        return {"matriculado": False}       # sin sección todavía: no hay cursos que mostrar

    id_alumno = ficha["id_alumno"]
    conducta = conducta_service.estado_conducta(usuario, id_alumno)
    return {
        "matriculado": True,
        "clases_de_hoy": _clases_de_hoy(usuario),
        "proximas_tareas": inicio_repository.proximas_tareas(id_alumno, matricula["id_seccion"], anio),
        "ultimas_notas": inicio_repository.ultimas_notas(matricula["id_matricula"]),
        "asistencia": asistencia_service.mi_asistencia(usuario)["resumen"],
        "conducta": {"bimestre": conducta["bimestre_actual"], "nota": conducta["nota_actual"]},
        "cita_activa": cita_repository.activa_de_alumno(id_alumno),
        "proximas_clases_virtuales": inicio_repository.proximas_clases_de_seccion(matricula["id_seccion"], anio),
    }
