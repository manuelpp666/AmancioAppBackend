"""Consultas SQL de la tabla `clase_virtual` (enlaces de clases en línea)."""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar

_COLUMNAS = "id_clase_virtual, id_carga_academica, tema, fecha, enlace, fecha_creacion"


def listar(id_carga: int) -> list:
    """Clases de un curso, ordenadas por fecha (la más próxima primero)."""
    return consultar_todos(f"""
        SELECT {_COLUMNAS}
        FROM clase_virtual
        WHERE id_carga_academica = %s
        ORDER BY fecha
    """, (id_carga,))


def buscar(id_clase: int):
    return consultar_uno(f"SELECT {_COLUMNAS} FROM clase_virtual WHERE id_clase_virtual = %s",
                         (id_clase,))


def crear(id_carga: int, tema, fecha, enlace: str) -> int:
    return insertar("""
        INSERT INTO clase_virtual (id_carga_academica, tema, fecha, enlace)
        VALUES (%s, %s, %s, %s)
    """, (id_carga, tema, fecha, enlace))


def actualizar(id_clase: int, tema, fecha, enlace: str) -> int:
    return ejecutar("""
        UPDATE clase_virtual
        SET tema = %s, fecha = %s, enlace = %s
        WHERE id_clase_virtual = %s
    """, (tema, fecha, enlace, id_clase))


def eliminar(id_clase: int) -> int:
    return ejecutar("DELETE FROM clase_virtual WHERE id_clase_virtual = %s", (id_clase,))
