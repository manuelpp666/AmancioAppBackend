"""Punto de entrada del servidor.

En la PC:     python run.py          (servidor de desarrollo en el puerto 5000)
En Render:    gunicorn run:app       (servidor de producción)
"""
import os

from app import config, create_app

# Se construye la aplicación una sola vez. Gunicorn busca esta variable `app`.
app = create_app()

if __name__ == "__main__":
    # host="0.0.0.0" permite que el celular (en la misma red WiFi) llegue a la PC.
    # debug=True recarga el servidor solo al guardar cambios (solo en desarrollo).
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=not config.ES_PRODUCCION)
