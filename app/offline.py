"""Decorador @idempotente: soporte para operaciones hechas sin conexión.

Se pone en las rutas que la app puede enviar sin internet y reintentar después:

    @bp.post("/item/<int:id_tarea>/entregar")
    @jwt_required("ALUMNO")
    @idempotente                      ← va DEBAJO de @jwt_required (necesita el usuario)
    def entregar(id_tarea): ...

Si la petición trae la cabecera  X-Id-Operacion: <id único>
    1.ª vez  → se ejecuta normal y, si salió bien (2xx), se guarda la respuesta.
    otra vez → NO se ejecuta: se devuelve la respuesta guardada, con la cabecera
               X-Operacion-Repetida: true.
Sin la cabecera, la ruta funciona exactamente igual que siempre.
"""
from functools import wraps

from flask import current_app, make_response, request

from app.auth import usuario_actual
from app.services import offline_service

CABECERA = "X-Id-Operacion"


def idempotente(ruta):
    @wraps(ruta)
    def ruta_idempotente(*args, **kwargs):
        id_operacion = request.headers.get(CABECERA)
        if not id_operacion:
            return ruta(*args, **kwargs)                 # petición normal

        usuario = usuario_actual()
        offline_service.validar_id(id_operacion)         # 400 si el formato es malo
        previa = offline_service.respuesta_previa(usuario, id_operacion)
        if previa is not None:
            # Reintento: misma respuesta que la primera vez, sin ejecutar nada.
            respuesta = current_app.response_class(previa["respuesta"], status=previa["codigo"],
                                                   mimetype="application/json")
            respuesta.headers["X-Operacion-Repetida"] = "true"
            return respuesta

        respuesta = make_response(ruta(*args, **kwargs))   # 1.ª vez: se ejecuta
        if 200 <= respuesta.status_code < 300:
            offline_service.registrar(usuario, id_operacion, request.method, request.path,
                                      respuesta.status_code, respuesta.get_data(as_text=True))
        return respuesta
    return ruta_idempotente
