"""Reglas de las notas y la libreta.

Cómo funciona:
1. El docente registra las notas de una EVALUACIÓN (ej. "Práctica 1") para los
   alumnos de su curso, en un bimestre que esté ABIERTO.
2. El promedio del bimestre de cada alumno = promedio simple de sus evaluaciones.
3. Cuando termina el bimestre, el docente lo CIERRA: los promedios pasan a la
   libreta (resumen_nota) y las notas de ese bimestre ya no se pueden cambiar.
4. La libreta muestra solo los bimestres cerrados. Al cerrar el 4.º bimestre el
   curso queda APROBADO (promedio final >= 11) o DESAPROBADO.
"""
from datetime import date

from app.database import get_db
from app.errors import ApiError
from app.repositories import academico_repository, cursos_repository, nota_repository
from app.services import academico_service, cursos_service
from app.utils import entero, numero, texto

NOTA_MAXIMA = 20
NOTA_APROBATORIA = 11


# --- Ayudas -------------------------------------------------------------------

def _bimestre_o_actual(bimestre) -> int:
    """El bimestre pedido (1 a 4) o, si no se indicó, el bimestre en curso."""
    if bimestre is None:
        anio = academico_service.anio_activo()
        actual = academico_repository.bimestre_de_fecha(anio["id_anio_escolar"], date.today())
        return actual["numero"] if actual else 1
    if not 1 <= bimestre <= 4:
        raise ApiError(400, "El bimestre debe estar entre 1 y 4")
    return bimestre


def _promedio(valores: list):
    """Promedio simple redondeado a 2 decimales, o None si no hay notas."""
    if not valores:
        return None
    return round(sum(float(v) for v in valores) / len(valores), 2)


def _curso_del_docente(usuario: dict, id_carga: int) -> dict:
    """El curso, comprobando que quien pide es su docente (el ADMIN solo puede ver)."""
    carga = cursos_service.buscar_carga(id_carga)
    if usuario["rol"] != "ADMIN":
        cursos_service.exigir_docente_del_curso(usuario, carga)
    return carga


# --- Docente --------------------------------------------------------------------

def notas_del_curso(usuario: dict, id_carga: int, bimestre=None) -> dict:
    """Registro de notas de un curso en un bimestre: cada alumno con sus evaluaciones."""
    carga = _curso_del_docente(usuario, id_carga)
    bimestre = _bimestre_o_actual(bimestre)

    # Las filas llegan una por alumno y evaluación: se agrupan por alumno.
    alumnos = {}
    for fila in nota_repository.notas_del_curso(carga["id_curso"], carga["id_seccion"],
                                                carga["anio"], bimestre):
        alumno = alumnos.setdefault(fila["id_alumno"], {
            "id_alumno": fila["id_alumno"], "nombres": fila["nombres"],
            "apellidos": fila["apellidos"], "evaluaciones": []})
        if fila["evaluacion"] is not None:          # LEFT JOIN: puede no tener notas
            alumno["evaluaciones"].append({"evaluacion": fila["evaluacion"], "valor": fila["valor"]})
    for alumno in alumnos.values():
        alumno["promedio"] = _promedio([e["valor"] for e in alumno["evaluaciones"]])

    return {
        "curso": carga,
        "bimestre": bimestre,
        "cerrado": bimestre in nota_repository.bimestres_cerrados(id_carga),
        "alumnos": list(alumnos.values()),
    }


def registrar_notas(usuario: dict, id_carga: int, datos: dict) -> dict:
    """Registra (o corrige) las notas de UNA evaluación para varios alumnos.
    Todo en una transacción: se guardan todas las notas o ninguna."""
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_docente_del_curso(usuario, carga)

    # 1. Validar los datos generales.
    bimestre = entero(datos, "bimestre", minimo=1, maximo=4)
    evaluacion = texto(datos, "evaluacion", minimo=2, maximo=20)   # ej. "Práctica 1"
    lista = datos.get("notas")
    if not isinstance(lista, list) or not lista:
        raise ApiError(400, "El campo 'notas' debe ser una lista con al menos un alumno")

    # 2. Regla: un bimestre cerrado ya no se puede modificar.
    if bimestre in nota_repository.bimestres_cerrados(id_carga):
        raise ApiError(409, f"El bimestre {bimestre} ya está cerrado: no se pueden cambiar sus notas")

    # 3. Validar cada nota.
    matriculados = {a["id_alumno"]: a for a in
                    cursos_repository.alumnos_de_seccion(carga["id_seccion"], carga["anio"])}
    notas = {}   # id_alumno → valor
    for item in lista:
        if not isinstance(item, dict):
            raise ApiError(400, "Cada nota debe ser un objeto con id_alumno y valor")
        id_alumno = entero(item, "id_alumno", minimo=1, maximo=2_000_000_000)
        valor = numero(item, "valor", minimo=0, maximo=NOTA_MAXIMA)
        if id_alumno not in matriculados:
            raise ApiError(400, f"El alumno {id_alumno} no está matriculado en este curso")
        if id_alumno in notas:
            raise ApiError(400, f"El alumno {id_alumno} aparece dos veces")
        notas[id_alumno] = valor

    # 4. Guardar todo en una TRANSACCIÓN.
    db = get_db()
    try:
        for id_alumno, valor in notas.items():
            nota_repository.guardar_nota(matriculados[id_alumno]["id_matricula"], carga["id_curso"],
                                         bimestre, evaluacion, valor)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Notas registradas", "curso": carga["curso"], "bimestre": bimestre,
            "evaluacion": evaluacion, "registradas": len(notas)}


def aplicar_cierre(carga: dict, bimestre: int, id_usuario: int) -> int:
    """Pasa los promedios del bimestre a la libreta y marca el bimestre como cerrado.
    NO hace commit: lo hace quien la llama (cerrar_bimestre o los datos de prueba)."""
    promedios = nota_repository.promedios_del_bimestre(carga["id_curso"], carga["id_seccion"],
                                                       carga["anio"], bimestre)
    if not promedios:
        raise ApiError(400, "El curso no tiene alumnos matriculados")
    # Regla: todos los alumnos deben tener al menos una nota en el bimestre.
    sin_notas = [f"{p['nombres']} {p['apellidos']}" for p in promedios if p["evaluaciones"] == 0]
    if sin_notas:
        raise ApiError(400, "Faltan notas de: " + ", ".join(sin_notas))

    for p in promedios:
        nota_repository.guardar_promedio_bimestre(p["id_matricula"], carga["id_curso"],
                                                  bimestre, p["promedio"])
        actualizar_promedio_final(p["id_matricula"], carga["id_curso"])
    nota_repository.registrar_cierre(carga["id_carga_academica"], bimestre, id_usuario)
    return len(promedios)


def actualizar_promedio_final(id_matricula: int, id_curso: int) -> None:
    """Promedio final = promedio de los bimestres cerrados. Con el 4.º cerrado,
    el curso queda APROBADO (>= 11) o DESAPROBADO; antes, EN CURSO. No hace commit."""
    fila = nota_repository.resumen(id_matricula, id_curso)
    cerrados = [fila[f"nota_bimestre{i}"] for i in range(1, 5) if fila[f"nota_bimestre{i}"] is not None]
    promedio_final = _promedio(cerrados)
    if fila["nota_bimestre4"] is None:
        estado = "EN CURSO"
    elif promedio_final >= NOTA_APROBATORIA:
        estado = "APROBADO"
    else:
        estado = "DESAPROBADO"
    nota_repository.actualizar_promedio_final(id_matricula, id_curso, promedio_final, estado)


def cerrar_bimestre(usuario: dict, id_carga: int, datos: dict) -> dict:
    carga = cursos_service.buscar_carga(id_carga)
    cursos_service.exigir_docente_del_curso(usuario, carga)
    bimestre = entero(datos, "bimestre", minimo=1, maximo=4)
    if bimestre in nota_repository.bimestres_cerrados(id_carga):
        raise ApiError(409, f"El bimestre {bimestre} ya estaba cerrado")

    # TRANSACCIÓN: un promedio por alumno + el registro del cierre. Todo o nada.
    db = get_db()
    try:
        total = aplicar_cierre(carga, bimestre, usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": f"Bimestre {bimestre} cerrado", "curso": carga["curso"], "alumnos": total}


# --- Alumno ---------------------------------------------------------------------

def _matricula_del_alumno(usuario: dict) -> dict:
    matricula = cursos_service.matricula_actual(usuario["id"])
    if matricula is None or matricula["id_seccion"] is None:
        raise ApiError(404, "No estás matriculado en una sección del año activo")
    return matricula


def mis_notas(usuario: dict, bimestre=None) -> dict:
    """Los cursos del alumno con sus evaluaciones y su promedio en un bimestre."""
    matricula = _matricula_del_alumno(usuario)
    bimestre = _bimestre_o_actual(bimestre)
    anio = academico_service.anio_activo()

    notas = nota_repository.notas_de_alumno(matricula["id_matricula"], bimestre)
    cursos = []
    for curso in cursos_repository.cursos_de_seccion(matricula["id_seccion"], anio["id_anio_escolar"]):
        evaluaciones = [{"evaluacion": n["evaluacion"], "valor": n["valor"]}
                        for n in notas if n["id_curso"] == curso["id_curso"]]
        cursos.append({
            "id_carga_academica": curso["id_carga_academica"],
            "curso": curso["curso"],
            "docente": curso["docente"],
            "evaluaciones": evaluaciones,
            "promedio": _promedio([e["valor"] for e in evaluaciones]),
        })
    return {"bimestre": bimestre, "cursos": cursos}


def mi_libreta(usuario: dict) -> dict:
    """Libreta: promedios de los bimestres cerrados y el promedio final de cada curso."""
    matricula = _matricula_del_alumno(usuario)
    anio = academico_service.anio_activo()
    return {"anio": anio["id_anio_escolar"],
            "cursos": nota_repository.libreta(matricula["id_matricula"])}
