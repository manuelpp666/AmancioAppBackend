"""Módulo Catálogo académico: listas de solo lectura (requieren iniciar sesión).

GET /academico/anio-activo              año escolar actual con sus 4 bimestres
GET /academico/grados                   niveles con sus grados
GET /academico/secciones?grado=<id>     secciones del año actual (filtro opcional)
GET /academico/cursos                   cursos con su área
"""
from flask import Blueprint, jsonify, request

from app.auth import jwt_required
from app.services import academico_service

bp = Blueprint("academico", __name__, url_prefix="/academico")


@bp.get("/anio-activo")
@jwt_required()
def anio_activo():
    return jsonify(academico_service.ver_anio_activo())


@bp.get("/grados")
@jwt_required()
def grados():
    return jsonify(academico_service.grados())


@bp.get("/secciones")
@jwt_required()
def secciones():
    id_grado = request.args.get("grado", type=int)   # ?grado=9 (opcional)
    return jsonify(academico_service.secciones(id_grado))


@bp.get("/cursos")
@jwt_required()
def cursos():
    return jsonify(academico_service.cursos())
