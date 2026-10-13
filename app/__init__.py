"""Campus AV Móvil — API REST en Flask + JWT.

Aquí se arma la aplicación: configuración, base de datos, manejo de errores,
rutas (blueprints) y comandos de consola.
"""
import os
import time

# Zona horaria del colegio (Lima). Va al inicio, antes de calcular cualquier fecha:
# los servidores en la nube trabajan en UTC (5 horas adelante) y sin esto, a las
# 7 pm en Lima el servidor creería que ya es el día siguiente.
# `time.tzset` solo existe en Linux; en Windows esta parte se salta.
if hasattr(time, "tzset"):
    os.environ["TZ"] = "America/Lima"
    time.tzset()


def create_app():
    """Crea y configura la aplicación Flask (patrón "application factory")."""
    from flask import Flask, jsonify

    from app import config, database
    from app.errors import registrar_errores
    from app.utils import ProveedorJSON

    # 1. Revisar que el archivo .env tenga lo necesario (si no, falla con un mensaje claro).
    config.verificar()

    # 2. Crear la app y decirle cómo convertir fechas y decimales a JSON.
    app = Flask(__name__)
    app.json = ProveedorJSON(app)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_MB * 1024 * 1024  # tope por petición

    # 3. Conectar con MySQL y registrar todas las tablas (modelos).
    database.init_db()
    from app import models  # noqa: F401
    # Al terminar cada petición se cierra su sesión de base de datos.
    app.teardown_appcontext(database.cerrar_sesion)

    # 4. Todos los errores se responden en JSON: {"detail": "mensaje"}.
    registrar_errores(app)

    # 5. CORS: solo hace falta si la app se prueba en un navegador (Expo web).
    #    Desde el celular no se usa.
    if config.ALLOWED_ORIGINS:
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

    # 6. Registrar las rutas. Cada blueprint es un módulo con su prefijo de URL.
    from app.blueprints.academico_bp import bp as academico_bp
    from app.blueprints.auth_bp import bp as auth_bp
    from app.blueprints.cursos_bp import bp as cursos_bp
    from app.blueprints.dispositivos_bp import bp as dispositivos_bp
    from app.blueprints.material_bp import bp as material_bp
    from app.blueprints.perfil_bp import bp as perfil_bp
    app.register_blueprint(auth_bp)            # /usuarios      login y sesión
    app.register_blueprint(perfil_bp)          # /perfil        datos personales
    app.register_blueprint(dispositivos_bp)    # /dispositivos  notificaciones
    app.register_blueprint(academico_bp)       # /academico     año, grados, secciones, cursos
    app.register_blueprint(cursos_bp)          # /cursos        mis cursos
    app.register_blueprint(material_bp)        # /material      material de clase

    # Ruta de "salud": sirve para comprobar que el servidor está encendido.
    @app.get("/")
    def salud():
        return jsonify({"status": "ok", "servicio": "Campus AV Móvil API"})

    # 7. Comandos de consola para preparar la base de datos:
    #    flask --app run crear-tablas
    #    flask --app run datos-prueba
    @app.cli.command("crear-tablas")
    def crear_tablas():
        """Crea las tablas que falten en la base (no borra ni modifica nada)."""
        from app.base_nueva import crear_tablas
        tablas = crear_tablas()
        print(f"{len(tablas)} tablas listas: {', '.join(tablas)}")

    @app.cli.command("datos-prueba")
    def datos_prueba():
        """Agrega los usuarios de prueba que falten (ver app/base_nueva.py)."""
        from app.base_nueva import cargar_datos_prueba
        creados = cargar_datos_prueba()
        if creados:
            print("Creados: " + ", ".join(creados))
        else:
            print("Los datos de prueba ya existían.")

    return app
