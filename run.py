"""Punto de entrada del servidor.

En la PC:     python run.py          (servidor de desarrollo en el puerto 5000,
                                      con WebSocket para el tiempo real)
En Render:    gunicorn run:app       (servidor de producción; ahí la app usa la
                                      actualización cada pocos segundos)
"""
import os

from app import config, create_app
from app.tiempo_real import socketio

# Se construye la aplicación una sola vez. Gunicorn busca esta variable `app`.
app = create_app()

if __name__ == "__main__":
    # host="0.0.0.0" permite que el celular (en la misma red WiFi) llegue a la PC.
    # debug=True recarga el servidor solo al guardar cambios (solo en desarrollo).
    # socketio.run en vez de app.run: así el mismo servidor atiende la API y el WebSocket.
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")),
                 debug=not config.ES_PRODUCCION, allow_unsafe_werkzeug=True)
