"""Envío de notificaciones push a los celulares (servicio de Expo).

La app móvil está hecha con Expo: al iniciar sesión registra su token
("ExponentPushToken[...]") con POST /dispositivos/token. Para avisarle algo al
celular basta con mandar ese token, un título y un texto al servicio de Expo,
que se encarga de entregarlo por Firebase (Android) o Apple (iOS).

Solo se envía si PUSH_ACTIVO=1 en el .env. Si falla (sin internet, token viejo...)
no pasa nada grave: la notificación ya quedó guardada en la base y el usuario
la ve igual en GET /notificaciones.
"""
import json
import logging
import threading
import urllib.request

from app import config

EXPO_URL = "https://exp.host/--/api/v2/push/send"
_PREFIJOS_EXPO = ("ExponentPushToken[", "ExpoPushToken[")
_POR_ENVIO = 100            # Expo acepta hasta 100 mensajes por petición

log = logging.getLogger(__name__)


def es_token_expo(token: str) -> bool:
    """Solo se envía a tokens de Expo; cualquier otro (por ejemplo, de Firebase directo) se ignora."""
    return bool(token) and token.startswith(_PREFIJOS_EXPO)


def armar_mensaje(token: str, titulo: str, mensaje: str, datos: dict | None = None) -> dict:
    """Un mensaje para UN celular, en el formato del servicio de Expo."""
    return {
        "to": token,
        "title": titulo,
        "body": mensaje,
        "sound": "default",
        "priority": "high",        # que llegue aunque el celular esté en reposo
        "channelId": "default",    # canal de Android que crea la app al pedir permiso
        "data": datos or {},       # la app lo usa para abrir la pantalla relacionada
    }


def armar_mensajes(tokens: list, titulo: str, mensaje: str, datos: dict | None = None) -> list:
    """El mismo mensaje para varios celulares (los tokens que no son de Expo se ignoran)."""
    return [armar_mensaje(token, titulo, mensaje, datos) for token in tokens if es_token_expo(token)]


def _enviar_ahora(mensajes: list) -> None:
    for i in range(0, len(mensajes), _POR_ENVIO):
        cuerpo = json.dumps(mensajes[i:i + _POR_ENVIO]).encode("utf-8")
        peticion = urllib.request.Request(EXPO_URL, data=cuerpo, method="POST",
                                          headers={"Content-Type": "application/json",
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(peticion, timeout=5) as respuesta:
                respuesta.read()
        except Exception as error:   # no se cae nada: la notificación ya está en la base
            log.warning("No se pudo enviar la notificación push: %s", error)


def enviar_mensajes(mensajes: list) -> int:
    """Envía mensajes ya armados (con armar_mensaje) en segundo plano.
    Devuelve cuántos se van a enviar (0 si el push está apagado o no hay tokens válidos)."""
    validos = [m for m in mensajes if es_token_expo(m.get("to", ""))]
    if not config.PUSH_ACTIVO or not validos:
        return 0
    threading.Thread(target=_enviar_ahora, args=(validos,), daemon=True).start()
    return len(validos)


def enviar(tokens: list, titulo: str, mensaje: str, datos: dict | None = None) -> int:
    """Envía la notificación a esos celulares en segundo plano (no hace esperar al usuario).
    Devuelve cuántos mensajes se van a enviar (0 si el push está apagado)."""
    mensajes = armar_mensajes(tokens, titulo, mensaje, datos)
    return enviar_mensajes(mensajes)
