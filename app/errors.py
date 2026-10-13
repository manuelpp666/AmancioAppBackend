"""Manejo de errores: toda respuesta de error sale en JSON con la forma
    {"detail": "mensaje"}
para que la app móvil siempre lea el mensaje del mismo lugar.

Códigos que usa la API:
    400 datos mal enviados          401 sin sesión o token inválido
    403 sin permiso                 404 no encontrado
    409 conflicto (ya existe, estado que no permite la acción)
    500 error del servidor          503 la base de datos no responde
"""
import pymysql
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Error que un service o una ruta lanza a propósito. Ejemplo:
        raise ApiError(404, "Usuario no encontrado")
    """
    def __init__(self, status: int, detail: str, headers: dict | None = None):
        super().__init__(detail)
        self.status = status            # código HTTP (400, 401, 403, 404, 409...)
        self.detail = detail            # mensaje para el usuario
        self.headers = headers or {}    # cabeceras extra (opcional)


def _respuesta(status: int, detail: str):
    resp = jsonify({"detail": detail})
    resp.status_code = status
    return resp


def registrar_errores(app) -> None:
    """Le dice a Flask cómo responder cada tipo de error."""

    @app.errorhandler(ApiError)
    def error_de_la_api(e: ApiError):
        # Errores que lanzamos nosotros con `raise ApiError(...)`.
        resp = _respuesta(e.status, e.detail)
        resp.headers.update(e.headers)
        return resp

    @app.errorhandler(pymysql.err.IntegrityError)
    def error_de_integridad(e):
        # MySQL rechazó el cambio: un valor UNIQUE repetido o una clave foránea
        # que apunta a algo que no existe.
        return _respuesta(409, "El registro ya existe o hace referencia a datos inexistentes")

    @app.errorhandler(pymysql.err.OperationalError)
    def error_de_conexion(e):
        # MySQL apagado, contraseña incorrecta en el .env, etc.
        app.logger.exception("No se pudo usar la base de datos")
        return _respuesta(503, "No se pudo conectar con la base de datos")

    @app.errorhandler(HTTPException)
    def error_http(e: HTTPException):
        # Errores propios de Flask, como 404 (ruta que no existe) o 405 (método equivocado).
        return _respuesta(e.code, e.description)

    @app.errorhandler(Exception)
    def error_inesperado(e: Exception):
        # Cualquier otro fallo (un bug). Se guarda el detalle en el log del servidor,
        # pero al usuario no se le muestra, para no revelar información interna.
        app.logger.exception("Error no controlado")
        return _respuesta(500, "Error interno del servidor")
