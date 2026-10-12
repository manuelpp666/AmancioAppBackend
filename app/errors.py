"""Manejo de errores: toda respuesta de error sale en JSON con la forma
    {"detail": "mensaje"}
para que la app móvil siempre lea el mensaje del mismo lugar.

Códigos que usa la API:
    400 datos mal enviados     401 sin sesión o token inválido
    403 sin permiso            404 no encontrado          500 error del servidor
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Error que una ruta lanza a propósito. Ejemplo:
        raise ApiError(404, "Usuario no encontrado")
    """
    def __init__(self, status: int, detail: str, headers: dict | None = None):
        super().__init__(detail)
        self.status = status            # código HTTP (400, 401, 403, 404...)
        self.detail = detail            # mensaje para el usuario
        self.headers = headers or {}    # cabeceras extra (opcional)


def registrar_errores(app) -> None:
    """Le dice a Flask cómo responder cada tipo de error."""

    @app.errorhandler(ApiError)
    def error_de_la_api(e: ApiError):
        # Errores que lanzamos nosotros con `raise ApiError(...)`.
        resp = jsonify({"detail": e.detail})
        resp.status_code = e.status
        resp.headers.update(e.headers)
        return resp

    @app.errorhandler(HTTPException)
    def error_http(e: HTTPException):
        # Errores propios de Flask, como 404 (ruta que no existe) o 405 (método equivocado).
        resp = jsonify({"detail": e.description})
        resp.status_code = e.code
        return resp

    @app.errorhandler(Exception)
    def error_inesperado(e: Exception):
        # Cualquier otro fallo (un bug). Se guarda el detalle en el log del servidor,
        # pero al usuario no se le muestra, para no revelar información interna.
        app.logger.exception("Error no controlado")
        resp = jsonify({"detail": "Error interno del servidor"})
        resp.status_code = 500
        return resp
