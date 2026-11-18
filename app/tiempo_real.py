"""Tiempo real con WebSocket (Socket.IO): mensajes y notificaciones al instante.

Cómo funciona:
1. Al iniciar sesión, la app abre una conexión WebSocket con el servidor y envía su
   token JWT. Si el token es válido, el servidor la mete en la "sala" de ese usuario
   (usuario:5). Si no, rechaza la conexión.
2. Cuando pasa algo (llega un mensaje, se crea una notificación...), el service lo
   ANOTA con `anotar(...)`. Al terminar la petición, si salió bien (después del
   commit), se envía por el WebSocket a la sala de cada usuario (`enviar_pendientes`).
   Así nadie recibe algo que después se deshizo con un rollback.
3. La app recibe el evento y actualiza la pantalla sin preguntar nada.

Eventos que envía el servidor:
    "mensaje"       {id_conversacion, mensaje: {id_mensaje, remitente_id, contenido, fecha_envio, leido, mio}}
    "leido"         {id_conversacion, leidos_hasta}   el otro leyó mis mensajes (hasta ese id)
    "notificacion"  {id_notificacion, tipo, titulo, mensaje, id_referencia, mostrar, push_enviado}
                    mostrar = el usuario no la silenció (ver preferencias);
                    push_enviado = además se envió como push al celular.

Funciona con el servidor de desarrollo (python run.py), que es lo que se usa en local.
Si se apaga (TIEMPO_REAL_ACTIVO=0) o no se puede conectar, la app sigue funcionando:
pregunta cada pocos segundos (ver src/config/tiempoReal.js en la app).
"""
import json
import logging

from flask import current_app, g
from flask_socketio import ConnectionRefusedError, SocketIO, join_room

from app import config
from app.auth import _validar_token
from app.errors import ApiError

log = logging.getLogger(__name__)

# "threading": funciona con el servidor de Flask, sin instalar eventlet ni gevent.
socketio = SocketIO(async_mode="threading", logger=False, engineio_logger=False)


def iniciar(app) -> None:
    """Conecta Socket.IO con la app de Flask (lo llama create_app).

    Se acepta cualquier origen ("*"): el celular envía como "Origin" la dirección del
    servidor (por ejemplo http://192.168.18.64:5000), que no está en ALLOWED_ORIGINS.
    La seguridad no depende del origen: sin un token JWT válido se rechaza la conexión.
    """
    socketio.init_app(app, cors_allowed_origins="*")


def sala(id_usuario: int) -> str:
    """Cada usuario tiene su sala: ahí reciben sus eventos todos sus dispositivos."""
    return f"usuario:{id_usuario}"


@socketio.on("connect")
def _al_conectar(auth=None):
    """La app se conecta enviando {"token": "<JWT>"}. Sin token válido, se rechaza."""
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        raise ConnectionRefusedError("Falta el token")
    try:
        usuario = _validar_token(token)
    except ApiError as error:
        raise ConnectionRefusedError(error.detail)
    join_room(sala(usuario["id"]))


# --- Enviar eventos -------------------------------------------------------------------

def _a_json(datos: dict) -> dict:
    """Convierte fechas y decimales de MySQL a texto/números (como en las respuestas)."""
    return json.loads(current_app.json.dumps(datos))


def anotar(id_usuarios: list, evento: str, datos: dict) -> None:
    """Deja un evento para enviarlo AL FINAL de la petición (solo si salió bien).
    Se usa dentro de las transacciones de los services, antes del commit."""
    if config.TIEMPO_REAL_ACTIVO:
        g.setdefault("eventos_tiempo_real", []).append((list(id_usuarios), evento, _a_json(datos)))


def emitir(id_usuarios: list, evento: str, datos: dict) -> None:
    """Envía un evento YA (usar solo después del commit). Nunca lanza errores."""
    if not config.TIEMPO_REAL_ACTIVO:
        return
    datos = _a_json(datos)
    for id_usuario in id_usuarios:
        try:
            socketio.emit(evento, datos, to=sala(id_usuario))
        except Exception as error:     # noqa: BLE001 — un fallo aquí no debe romper la respuesta
            log.warning("No se pudo enviar '%s' al usuario %s: %s", evento, id_usuario, error)


def enviar_pendientes() -> None:
    """Envía los eventos anotados durante la petición (lo llama app/__init__.py)."""
    for id_usuarios, evento, datos in g.pop("eventos_tiempo_real", []):
        for id_usuario in id_usuarios:
            try:
                socketio.emit(evento, datos, to=sala(id_usuario))
            except Exception as error:     # noqa: BLE001
                log.warning("No se pudo enviar '%s' al usuario %s: %s", evento, id_usuario, error)
