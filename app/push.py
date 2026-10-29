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


def armar_mensajes(tokens: list, titulo: str, mensaje: str, datos: dict | None = None) -> list:
    """Un mensaje por cada token de Expo (los tokens de otro tipo se ignoran)."""
    return [{"to": token, "title": titulo, "body": mensaje, "sound": "default", "data": datos or {}}
            for token in tokens if token.startswith(_PREFIJOS_EXPO)]


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


def enviar(tokens: list, titulo: str, mensaje: str, datos: dict | None = None) -> int:
    """Envía la notificación a esos celulares en segundo plano (no hace esperar al usuario).
    Devuelve cuántos mensajes se van a enviar (0 si el push está apagado)."""
    mensajes = armar_mensajes(tokens, titulo, mensaje, datos)
    if not config.PUSH_ACTIVO or not mensajes:
        return 0
    threading.Thread(target=_enviar_ahora, args=(mensajes,), daemon=True).start()
    return len(mensajes)
