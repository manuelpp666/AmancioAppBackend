"""Actualizar una base de datos que YA existe a la versión actual del código.

database/schema.sql usa CREATE TABLE IF NOT EXISTS: crea las tablas NUEVAS, pero
no toca las que ya estaban. Por eso las columnas que se agregan a una tabla
existente se anotan aquí, en COLUMNAS_NUEVAS, y se agregan con ALTER TABLE solo
si todavía no existen.

Se ejecuta:
  - solo, al encender el servidor (si ACTUALIZAR_BASE_AL_INICIAR=1, que es lo normal);
  - a mano con:  flask --app run crear-tablas

Nunca borra nada: solo crea tablas y agrega columnas que falten.

Para agregar una columna nueva en el futuro:
  1. Agrégala en el CREATE TABLE de database/schema.sql (para las bases nuevas).
  2. Agrégala en COLUMNAS_NUEVAS (para las bases que ya existen).
"""
import logging

import pymysql

from app.database import consultar_uno, get_db

log = logging.getLogger(__name__)

ARCHIVO_SCHEMA = "database/schema.sql"

# (tabla, columna, definición SQL de la columna)
COLUMNAS_NUEVAS = [
    # Asistencia: qué tenía el alumno (T o F) antes de que se justificara.
    ("asistencia", "estado_original", "VARCHAR(1) NULL DEFAULT NULL AFTER `estado`"),
    # Tareas: archivo subido como enunciado (tabla `archivo`).
    ("tarea", "id_archivo", "INT(11) NULL DEFAULT NULL AFTER `archivo_adjunto_url`"),
    # Entregas: archivo que subió el alumno (PDF, Word, imagen...).
    ("entrega_tarea", "id_archivo", "INT(11) NULL DEFAULT NULL AFTER `archivo_url`"),
]

_COLUMNA_REPETIDA = 1060    # código de MySQL: "Duplicate column name"


def _existe_columna(tabla: str, columna: str) -> bool:
    fila = consultar_uno("""
        SELECT COUNT(*) AS total FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (tabla, columna))
    return fila["total"] > 0


def crear_tablas() -> int:
    """Ejecuta cada sentencia de database/schema.sql. Devuelve cuántas ejecutó."""
    with open(ARCHIVO_SCHEMA, encoding="utf-8") as archivo:
        # Se quitan las líneas de comentario y se separa por ";".
        lineas = [l for l in archivo if not l.strip().startswith("--")]
    sentencias = [s.strip() for s in "".join(lineas).split(";") if s.strip()]

    db = get_db()
    with db.cursor() as cursor:
        for sentencia in sentencias:
            cursor.execute(sentencia)
    db.commit()
    return len(sentencias)


def agregar_columnas() -> list[str]:
    """Agrega las columnas de COLUMNAS_NUEVAS que falten. Devuelve las que agregó."""
    agregadas = []
    db = get_db()
    for tabla, columna, definicion in COLUMNAS_NUEVAS:
        if _existe_columna(tabla, columna):
            continue
        try:
            with db.cursor() as cursor:
                cursor.execute(f"ALTER TABLE `{tabla}` ADD COLUMN `{columna}` {definicion}")
            agregadas.append(f"{tabla}.{columna}")
        except pymysql.err.OperationalError as error:
            # Otro proceso del servidor la agregó al mismo tiempo: no es un problema.
            if error.args[0] != _COLUMNA_REPETIDA:
                raise
    db.commit()
    return agregadas


def actualizar_base() -> list[str]:
    """Crea las tablas que falten y agrega las columnas nuevas. Devuelve lo que cambió."""
    crear_tablas()
    return agregar_columnas()


def actualizar_al_iniciar(app) -> None:
    """Se llama al crear la app. Si la base no responde, el servidor arranca igual
    (las rutas responderán 503) y se anota el problema en el log."""
    try:
        with app.app_context():
            agregadas = actualizar_base()
        if agregadas:
            log.warning("Base de datos actualizada, columnas nuevas: %s", ", ".join(agregadas))
    except Exception as error:     # noqa: BLE001 — nunca debe impedir que arranque el servidor
        log.warning("No se pudo actualizar la base de datos al iniciar: %s", error)
