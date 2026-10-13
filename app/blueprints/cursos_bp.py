"""Módulo Mis cursos: cada usuario ve sus cursos del año actual.

GET /cursos/mis-cursos                 alumno: cursos de su sección · docente: cursos que dicta
GET /cursos/<id_carga>/alumnos         docente (o ADMIN): alumnos matriculados en ese curso

Un "curso" aquí es una carga académica (ver app/services/cursos.py).
"""
from flask import Blueprint, jsonify

from app.auth import jwt_required, usuario_actual
from app.database import get_db
from app.models.alumno import Alumno
from app.models.gestion import CargaAcademica
from app.models.matricula import Matricula
from app.services import cursos

bp = Blueprint("cursos", __name__, url_prefix="/cursos")


@bp.get("/mis-cursos")
@jwt_required("ALUMNO", "DOCENTE")
def mis_cursos():
    db = get_db()
    anio = cursos.anio_activo(db)
    yo = usuario_actual()

    # Solo los cursos del año actual.
    consulta = db.query(CargaAcademica).filter(
        CargaAcademica.id_anio_escolar == anio.id_anio_escolar)

    if yo["rol"] == "ALUMNO":
        # Alumno: los cursos de la sección donde está matriculado este año.
        alumno = cursos.alumno_de(db, yo["id"])
        matricula = cursos.matricula_del_anio(db, alumno.id_alumno, anio.id_anio_escolar) if alumno else None
        if matricula is None or matricula.id_seccion is None:
            return jsonify([])   # todavía no está matriculado en una sección
        consulta = consulta.filter(CargaAcademica.id_seccion == matricula.id_seccion)
    else:
        # Docente: los cursos que él dicta.
        docente = cursos.docente_de(db, yo["id"])
        if docente is None:
            return jsonify([])
        consulta = consulta.filter(CargaAcademica.id_docente == docente.id_docente)

    return jsonify([cursos.curso_a_dict(carga) for carga in consulta.all()])


@bp.get("/<int:id_carga>/alumnos")
@jwt_required("DOCENTE", "ADMIN")
def alumnos_del_curso(id_carga):
    db = get_db()
    carga = cursos.buscar_carga(db, id_carga)

    # Un docente solo puede ver los alumnos de SUS cursos (el ADMIN, de todos).
    if usuario_actual()["rol"] == "DOCENTE":
        cursos.exigir_docente_del_curso(db, carga)

    # Alumnos matriculados en la sección del curso, en el año del curso.
    alumnos = (db.query(Alumno)
               .join(Matricula, Matricula.id_alumno == Alumno.id_alumno)
               .filter(Matricula.id_seccion == carga.id_seccion,
                       Matricula.id_anio_escolar == carga.id_anio_escolar)
               .order_by(Alumno.apellidos, Alumno.nombres)
               .all())

    return jsonify({
        "curso": cursos.curso_a_dict(carga),
        "alumnos": [
            {"id_alumno": a.id_alumno, "dni": a.dni, "nombres": a.nombres, "apellidos": a.apellidos}
            for a in alumnos
        ],
    })
