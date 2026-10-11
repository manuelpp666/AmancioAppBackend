"""Punto de entrada.

Local:   python run.py
Render:  gunicorn run:app --workers 2 --bind 0.0.0.0:$PORT
"""
import os

from app import config, create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=not config.ES_PRODUCCION)
