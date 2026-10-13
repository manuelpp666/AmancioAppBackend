"""Campus AV Móvil — API REST en Flask + JWT + MySQL.

Arquitectura por capas:  Route → Service → Repository → Base de datos
    routes/        reciben la petición y devuelven JSON
    services/      validaciones, reglas de negocio y transacciones (COMMIT/ROLLBACK)
    repositories/  consultas SQL

Aquí se arma la aplicación: configuración, conexión, errores, rutas y comandos.
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

    # 2. Crear la app y decirle cómo convertir fechas, horas y decimales a JSON.
    app = Flask(__name__)
    app.json = ProveedorJSON(app)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_MB * 1024 * 1024  # tope por petición

    # 3. Al terminar cada petición se cierra su conexión con MySQL.
    app.teardown_appcontext(database.cerrar_db)

    # 4. Todos los errores se responden en JSON: {"detail": "mensaje"}.
    registrar_errores(app)

    # 5. CORS: solo hace falta si la app se prueba en un navegador (Expo web).
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

    # 6. Registrar las rutas: cada archivo de app/routes es un módulo con su prefijo.
    from app.routes import (academico_routes, asistencia_routes, auth_routes, cita_routes,
                            clase_routes, conducta_routes, cursos_routes, dispositivo_routes,
                            horario_routes, material_routes, nota_routes, perfil_routes,
                            tarea_routes)
    app.register_blueprint(auth_routes.bp)          # /usuarios      login y sesión
    app.register_blueprint(perfil_routes.bp)        # /perfil        datos personales y contraseña
    app.register_blueprint(dispositivo_routes.bp)   # /dispositivos  notificaciones
    app.register_blueprint(academico_routes.bp)     # /academico     año, grados, secciones, cursos
    app.register_blueprint(cursos_routes.bp)        # /cursos        mis cursos
    app.register_blueprint(material_routes.bp)      # /material      material de clase
    app.register_blueprint(clase_routes.bp)         # /clases        clases virtuales
    app.register_blueprint(tarea_routes.bp)         # /tareas        tareas, entregas y calificación
    app.register_blueprint(horario_routes.bp)       # /horario       horario escolar
    app.register_blueprint(asistencia_routes.bp)    # /asistencia    asistencia por sección
    app.register_blueprint(nota_routes.bp)          # /notas         notas, cierre de bimestre y libreta
    app.register_blueprint(conducta_routes.bp)      # /conducta      reportes y nota de conducta
    app.register_blueprint(cita_routes.bp)          # /citas         citas de psicología

    # Ruta de "salud": sirve para comprobar que el servidor está encendido.
    @app.get("/")
    def salud():
        return jsonify({"status": "ok", "servicio": "Campus AV Móvil API"})

    # 7. Comandos de consola para preparar la base de datos (ver app/datos_prueba.py).
    @app.cli.command("crear-tablas")
    def crear_tablas():
        """Ejecuta database/schema.sql (crea las tablas que falten, no borra nada)."""
        from app.datos_prueba import crear_tablas
        print(f"{crear_tablas()} sentencias ejecutadas desde database/schema.sql")

    @app.cli.command("datos-prueba")
    def datos_prueba():
        """Agrega los datos de prueba que falten."""
        from app.datos_prueba import cargar_datos_prueba
        creados = cargar_datos_prueba()
        print("Creados: " + ", ".join(creados) if creados else "Los datos de prueba ya existían.")

    @app.cli.command("reiniciar-demo")
    def reiniciar_demo():
        """Deja la demo como al principio: claves = DNI y bimestre 3 abierto."""
        from app.datos_prueba import reiniciar_demo
        reiniciar_demo()
        print("Demo reiniciada: contraseñas = DNI (Mateo en primer ingreso) y bimestres 3 y 4 abiertos.")

    return app
