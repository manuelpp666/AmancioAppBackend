"""Errores de la API. Todo error sale como JSON: {"detail": "mensaje"}.

El campo se llama `detail` (igual que en el backend original) para que el
interceptor de la app móvil lea siempre el mensaje del mismo sitio.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, detail: str, headers: dict | None = None):
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.headers = headers or {}


def registrar_errores(app) -> None:
    @app.errorhandler(ApiError)
    def _api_error(e: ApiError):
        resp = jsonify({"detail": e.detail})
        resp.status_code = e.status
        for k, v in e.headers.items():
            resp.headers[k] = v
        return resp

    @app.errorhandler(HTTPException)
    def _http_error(e: HTTPException):
        resp = jsonify({"detail": e.description})
        resp.status_code = e.code
        return resp

    @app.errorhandler(Exception)
    def _error_inesperado(e: Exception):
        app.logger.exception("Error no controlado")
        resp = jsonify({"detail": "Error interno del servidor"})
        resp.status_code = 500
        return resp
