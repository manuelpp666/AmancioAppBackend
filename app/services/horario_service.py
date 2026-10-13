"""Reglas del horario escolar: el alumno ve el de su sección y el docente el
de sus cursos, ordenado por día y hora."""
from app.errors import ApiError
from app.repositories import horario_repository, perfil_repository
from app.services import academico_service, cursos_service
from app.utils import hora_texto

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes"}


def mi_horario(usuario: dict) -> dict:
    anio = academico_service.anio_activo()

    if usuario["rol"] == "ALUMNO":
        matricula = cursos_service.matricula_actual(usuario["id"])
        if matricula is None or matricula["id_seccion"] is None:
            bloques = []
        else:
            bloques = horario_repository.de_seccion(matricula["id_seccion"], anio["id_anio_escolar"])
    else:
        docente = perfil_repository.docente_por_usuario(usuario["id"])
        if docente is None:
            raise ApiError(404, "Datos de docente no encontrados")
        bloques = horario_repository.de_docente(docente["id_docente"], anio["id_anio_escolar"])

    # Agrupar los bloques por día (los 5 días salen siempre, aunque estén vacíos).
    dias = [{"dia": nombre, "bloques": []} for nombre in DIAS.values()]
    for b in bloques:
        dias[b["dia_semana"] - 1]["bloques"].append({
            "hora_inicio": hora_texto(b["hora_inicio"]),
            "hora_fin": hora_texto(b["hora_fin"]),
            "curso": b["curso"],
            "detalle": b["detalle"],   # alumno: el docente · docente: la sección
        })

    recesos = [{"nombre": r["nombre"], "hora_inicio": hora_texto(r["hora_inicio"]),
                "hora_fin": hora_texto(r["hora_fin"])} for r in horario_repository.recesos()]
    return {"anio": anio["id_anio_escolar"], "dias": dias, "recesos": recesos}
