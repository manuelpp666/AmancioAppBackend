"""Campus AV Móvil — API REST en Flask + JWT sobre la base MySQL del campus web."""
import os
import time

# Zona horaria del colegio: TIENE QUE IR antes de que nada calcule una fecha.
# Render corre en UTC; sin esto, a las 7 pm de Lima el servidor ya cree que es
# el día siguiente y la asistencia/horario se desfasan. (Solo Linux: tzset.)
if hasattr(time, "tzset"):
    os.environ["TZ"] = "America/Lima"
    time.tzset()


def create_app():
    from flask import Flask, jsonify

    from app import config
    from app.errors import registrar_errores
    from app.utils import ProveedorJSON

    config.verificar()

    app = Flask(__name__)
    app.json = ProveedorJSON(app)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_MB * 1024 * 1024

    from app import database
    database.init_db()
    from app import models  # noqa: F401  (registra todas las tablas)
    app.teardown_appcontext(database.cerrar_sesion)

    registrar_errores(app)

    if config.ALLOWED_ORIGINS:   # solo hace falta si pruebas la app en navegador (Expo web)
        @app.after_request
        def _cors(resp):
            from flask import request
            origen = request.headers.get("Origin")
            if origen in config.ALLOWED_ORIGINS:
                resp.headers["Access-Control-Allow-Origin"] = origen
                resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                resp.headers["Vary"] = "Origin"
            return resp

    from app.blueprints.auth_bp import bp as auth_bp
    from app.blueprints.dispositivos_bp import bp as dispositivos_bp
    from app.blueprints.perfil_bp import bp as perfil_bp
    for bp in (auth_bp, perfil_bp, dispositivos_bp):
        app.register_blueprint(bp)

    @app.get("/")
    def salud():
        return jsonify({"status": "ok", "servicio": "Campus AV Móvil API"})

    @app.cli.command("crear-tabla-dispositivos")
    def crear_tabla_dispositivos():
        """Crea la tabla nueva `dispositivo_push` (no toca ninguna otra)."""
        from app.models.dispositivo import DispositivoPush
        DispositivoPush.__table__.create(bind=database.engine, checkfirst=True)
        print("Tabla dispositivo_push lista.")

    return app
