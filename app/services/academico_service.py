"""Reglas del catálogo académico (solo lectura)."""
from app.errors import ApiError
from app.repositories import academico_repository


def anio_activo() -> dict:
    """Año escolar en curso, o error 404 si no hay ninguno activo.
    Lo usan también otros services (cursos, asistencia, conducta, horario)."""
    anio = academico_repository.anio_activo()
    if anio is None:
        raise ApiError(404, "No hay un año escolar activo")
    return anio


def ver_anio_activo() -> dict:
    anio = anio_activo()
    anio["bimestres"] = academico_repository.bimestres(anio["id_anio_escolar"])
    return anio


def grados() -> list:
    """Niveles con la lista de sus grados: [{"nivel": "Primaria", "grados": [...]}, ...]"""
    niveles = []
    for fila in academico_repository.grados_con_nivel():
        # Las filas vienen ordenadas por nivel: si cambia el nivel, se abre uno nuevo.
        if not niveles or niveles[-1]["id_nivel"] != fila["id_nivel"]:
            niveles.append({"id_nivel": fila["id_nivel"], "nivel": fila["nivel"], "grados": []})
        niveles[-1]["grados"].append({"id_grado": fila["id_grado"], "nombre": fila["nombre"]})
    return niveles


def secciones(id_grado=None) -> list:
    anio = anio_activo()
    return academico_repository.secciones(anio["id_anio_escolar"], id_grado)


def cursos() -> list:
    return academico_repository.cursos()
