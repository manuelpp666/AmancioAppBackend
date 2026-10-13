"""Conexión a MySQL con PyMySQL y funciones para ejecutar SQL.

Cada petición HTTP usa UNA conexión, que se abre la primera vez que se pide
(`get_db`) y se cierra al terminar la petición (`cerrar_db`).

La conexión trabaja con autocommit desactivado: nada queda guardado hasta que
el Service hace `db.commit()`. Si algo falla, el Service hace `db.rollback()`
y se deshacen TODOS los cambios de esa operación (eso es una transacción).

Los repositories usan estas cuatro funciones:
    consultar_uno(sql, params)    SELECT que devuelve una fila (dict) o None
    consultar_todos(sql, params)  SELECT que devuelve una lista de filas (dicts)
    insertar(sql, params)         INSERT; devuelve el id de la fila creada
    ejecutar(sql, params)         UPDATE / DELETE; devuelve cuántas filas afectó

Los valores SIEMPRE van en `params` con %s, nunca pegados al texto del SQL:
así PyMySQL los escapa y se evita la inyección SQL.
"""
import pymysql
from flask import g
from pymysql.constants import CLIENT

from app import config


def _host_y_puerto():
    """DB_HOST puede venir como "127.0.0.1:3310"; se separa el host del puerto."""
    if ":" in config.DB_HOST:
        host, puerto = config.DB_HOST.rsplit(":", 1)
        return host, int(puerto)
    return config.DB_HOST, 3306


def conectar():
    """Abre una conexión nueva con MySQL."""
    host, puerto = _host_y_puerto()
    return pymysql.connect(
        host=host,
        port=puerto,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        charset="utf8mb4",                      # tildes, ñ y emojis
        cursorclass=pymysql.cursors.DictCursor,  # cada fila llega como dict {"columna": valor}
        autocommit=False,                        # los cambios se confirman con commit()
        # UPDATE devuelve las filas ENCONTRADAS por el WHERE (aunque el valor no
        # cambie), no solo las que cambiaron. Así "0" significa "no existe".
        client_flag=CLIENT.FOUND_ROWS,
    )


def get_db():
    """Conexión de la petición actual (se crea la primera vez que se pide).
    `g` es un espacio de Flask que dura solo lo que dura la petición."""
    if "db" not in g:
        g.db = conectar()
    return g.db


def cerrar_db(_error=None) -> None:
    """Se ejecuta al final de cada petición. Lo que no tuvo commit se descarta."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# --- Funciones que usan los repositories ------------------------------------

def consultar_uno(sql: str, params: tuple = ()):
    """SELECT que devuelve una sola fila (dict), o None si no hay resultados."""
    with get_db().cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def consultar_todos(sql: str, params: tuple = ()) -> list:
    """SELECT que devuelve todas las filas (lista de dicts; vacía si no hay)."""
    with get_db().cursor() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def insertar(sql: str, params: tuple = ()) -> int:
    """INSERT. Devuelve el id (AUTO_INCREMENT) de la fila creada."""
    with get_db().cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid


def ejecutar(sql: str, params: tuple = ()) -> int:
    """UPDATE o DELETE. Devuelve cuántas filas cumplieron el WHERE (0 = ninguna)."""
    with get_db().cursor() as cursor:
        return cursor.execute(sql, params)
