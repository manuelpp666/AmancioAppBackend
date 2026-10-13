"""Módulo Catálogo académico: listas de solo lectura que la app usa para mostrar
opciones (año escolar, grados, secciones y cursos). Requieren iniciar sesión.

GET /academico/anio-activo              año escolar actual con sus 4 bimestres
GET /academico/grados                   niveles (Primaria / Secundaria) con sus grados
GET /academico/secciones?grado=<id>     secciones del año actual (filtro opcional por grado)
GET /academico/cursos                   todos los cursos con su área
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required
from app.database import get_db
from app.models.academico import Curso, Grado, Nivel, Seccion
from app.services.cursos import anio_activo

bp = Blueprint("academico", __name__, url_prefix="/academico")


@bp.get("/anio-activo")
@jwt_required()
def ver_anio_activo():
    anio = anio_activo(get_db())
    return jsonify({
        "id_anio_escolar": anio.id_anio_escolar,
        "fecha_inicio": anio.fecha_inicio,
        "fecha_fin": anio.fecha_fin,
        "tipo": anio.tipo,
        "bimestres": [
            {"numero": b.numero, "fecha_inicio": b.fecha_inicio, "fecha_fin": b.fecha_fin}
            for b in anio.bimestres     # ya vienen ordenados por número
        ],
    })


@bp.get("/grados")
@jwt_required()
def listar_grados():
    niveles = get_db().query(Nivel).order_by(Nivel.id_nivel).all()
    # Cada nivel con la lista de sus grados (ordenados: 1ro, 2do, ...).
    return jsonify([
        {
            "id_nivel": nivel.id_nivel,
            "nivel": nivel.nombre,
            "grados": [{"id_grado": g.id_grado, "nombre": g.nombre} for g in nivel.grados],
        }
        for nivel in niveles
    ])


@bp.get("/secciones")
@jwt_required()
def listar_secciones():
    db = get_db()
    anio = anio_activo(db)

    # Solo las secciones del año actual.
    consulta = db.query(Seccion).filter(Seccion.id_anio_escolar == anio.id_anio_escolar)

    # Filtro opcional: /academico/secciones?grado=9
    id_grado = request.args.get("grado", type=int)
    if id_grado is not None:
        consulta = consulta.filter(Seccion.id_grado == id_grado)

    secciones = consulta.join(Grado).order_by(Grado.orden, Seccion.nombre).all()
    return jsonify([
        {
            "id_seccion": s.id_seccion,
            "nombre": s.nombre,
            "vacantes": s.vacantes,
            "id_grado": s.id_grado,
            "grado": s.grado.nombre,
            "nivel": s.grado.nivel.nombre,
        }
        for s in secciones
    ])


@bp.get("/cursos")
@jwt_required()
def listar_cursos():
    cursos = get_db().query(Curso).order_by(Curso.nombre).all()
    return jsonify([
        {
            "id_curso": c.id_curso,
            "nombre": c.nombre,
            "area": c.area.nombre if c.area else None,
        }
        for c in cursos
    ])
