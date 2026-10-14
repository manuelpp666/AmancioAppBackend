"""Reglas de la asistencia.

El auxiliar registra la asistencia de TODA una sección en una sola operación
(POST /asistencia/lote). Es una TRANSACCIÓN: se guardan todos los alumnos o
ninguno. Si algo falla a mitad de camino, el ROLLBACK deshace lo que ya se
había escrito y la base queda como estaba.

estado: P = presente, T = tardanza, F = falta, J = falta justificada.
"""
from datetime import date

from app.database import get_db
from app.errors import ApiError
from app.repositories import academico_repository, asistencia_repository, cursos_repository
from app.services import academico_service, cursos_service
from app.utils import entero, fecha, lista, texto

ESTADOS = ("P", "T", "F", "J")


def _resumen(conteos: list) -> dict:
    """[{"estado": "F", "total": 2}, ...]  →  {"P": 0, "T": 0, "F": 2, "J": 0}"""
    resumen = {estado: 0 for estado in ESTADOS}
    for fila in conteos:
        resumen[fila["estado"]] = fila["total"]
    return resumen


def registrar_lote(datos: dict) -> dict:
    # --- 1. Validar los datos generales ---------------------------------------
    id_seccion = entero(datos, "id_seccion", minimo=1, maximo=2_000_000_000)
    dia = fecha(datos, "fecha")
    if dia > date.today():
        raise ApiError(400, "No se puede registrar asistencia de una fecha futura")
    registros = lista(datos, "registros")        # 400 si no es lista o está vacía

    anio = academico_service.anio_activo()
    seccion = academico_repository.seccion_por_id(id_seccion)
    if seccion is None:
        raise ApiError(404, "Sección no encontrada")
    if seccion["id_anio_escolar"] != anio["id_anio_escolar"]:
        raise ApiError(400, "La sección no pertenece al año escolar activo")

    # Alumnos matriculados en la sección: {id_alumno: fila con id_matricula y nombre}
    matriculados = {a["id_alumno"]: a for a in
                    cursos_repository.alumnos_de_seccion(id_seccion, anio["id_anio_escolar"])}
    if not matriculados:
        raise ApiError(400, "La sección no tiene alumnos matriculados")

    # --- 2. Validar cada registro ----------------------------------------------
    marcados = {}   # id_alumno → (estado, observacion)
    for registro in registros:
        if not isinstance(registro, dict):
            raise ApiError(400, "Cada registro debe ser un objeto con id_alumno y estado")
        id_alumno = entero(registro, "id_alumno", minimo=1, maximo=2_000_000_000)
        estado = texto(registro, "estado", minimo=1, maximo=1).upper()
        observacion = texto(registro, "observacion", minimo=0, maximo=150, requerido=False) or None

        if estado not in ESTADOS:
            raise ApiError(400, f"Estado '{estado}' no válido: usa P, T, F o J")
        if id_alumno not in matriculados:
            raise ApiError(400, f"El alumno {id_alumno} no está matriculado en esta sección")
        if id_alumno in marcados:
            raise ApiError(400, f"El alumno {id_alumno} aparece dos veces")
        marcados[id_alumno] = (estado, observacion)

    # Regla del colegio: el registro debe estar COMPLETO (todos los alumnos).
    faltan = [f"{a['nombres']} {a['apellidos']}" for i, a in matriculados.items() if i not in marcados]
    if faltan:
        raise ApiError(400, "Falta registrar a: " + ", ".join(faltan))

    # --- 3. Guardar todo en una TRANSACCIÓN ------------------------------------
    db = get_db()
    try:
        # Si ya había asistencia de ese día, se reemplaza por la nueva.
        asistencia_repository.borrar_del_dia(id_seccion, dia)
        for id_alumno, (estado, observacion) in marcados.items():
            id_matricula = matriculados[id_alumno]["id_matricula"]
            asistencia_repository.registrar(id_matricula, dia, estado, observacion)
        db.commit()        # todo salió bien: se guardan TODOS los registros
    except Exception:
        db.rollback()      # algo falló: no se guarda NINGUNO
        raise

    conteo = {estado: 0 for estado in ESTADOS}
    for estado, _ in marcados.values():
        conteo[estado] += 1
    return {
        "message": "Asistencia registrada",
        "seccion": f"{seccion['grado']} {seccion['nombre']} - {seccion['nivel']}",
        "fecha": dia,
        "total": len(marcados),
        "resumen": conteo,
    }


def de_seccion(id_seccion: int, dia=None) -> dict:
    """Asistencia registrada de una sección en un día (por defecto, hoy)."""
    dia = dia or date.today()
    seccion = academico_repository.seccion_por_id(id_seccion)
    if seccion is None:
        raise ApiError(404, "Sección no encontrada")
    registros = asistencia_repository.de_seccion_y_fecha(id_seccion, dia)
    return {
        "seccion": f"{seccion['grado']} {seccion['nombre']} - {seccion['nivel']}",
        "fecha": dia,
        "registrada": len(registros) > 0,
        "registros": registros,
    }


def mi_asistencia(usuario: dict) -> dict:
    """Historial del alumno en el año activo, con el total de cada estado."""
    matricula = cursos_service.matricula_actual(usuario["id"])
    if matricula is None:
        return {"registros": [], "resumen": _resumen([])}
    return {
        "registros": asistencia_repository.de_matricula(matricula["id_matricula"]),
        "resumen": _resumen(asistencia_repository.resumen_de_matricula(matricula["id_matricula"])),
    }
