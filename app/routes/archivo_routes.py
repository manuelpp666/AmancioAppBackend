"""Módulo Archivos: abrir un archivo subido (enunciado de una tarea o entrega de un alumno).

GET /archivos/<id_archivo>?token=<token>     devuelve el archivo

No usa el JWT de la sesión: el `token` viene dentro de la `url` que la API devuelve
junto con cada tarea o entrega (ver app/services/archivo_service.py). Así el archivo
se puede abrir directamente en el navegador del celular.
"""
from flask import Blueprint, request, send_file

from app.services import archivo_service

bp = Blueprint("archivos", __name__, url_prefix="/archivos")


@bp.get("/<int:id_archivo>")
def abrir(id_archivo):
    archivo = archivo_service.para_abrir(id_archivo, request.args.get("token"))
    respuesta = send_file(
        archivo["ruta"],
        mimetype=archivo["tipo"],
        download_name=archivo["nombre"],
        as_attachment=not archivo["en_navegador"],    # PDF e imágenes se ven; el resto se descarga
        max_age=0,
    )
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Cache-Control"] = "private, no-store"
    return respuesta
