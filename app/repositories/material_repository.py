"""Consultas SQL de la tabla `material_clase`."""
from app.database import consultar_todos, consultar_uno, ejecutar, insertar

_COLUMNAS = """id_material, id_carga_academica, titulo, descripcion, archivo_url,
               bimestre, fecha_publicacion"""


def listar(id_carga: int, bimestre=None) -> list:
    """Material de un curso, el más reciente primero. Filtro opcional por bimestre."""
    sql = f"SELECT {_COLUMNAS} FROM material_clase WHERE id_carga_academica = %s"
    params = [id_carga]
    if bimestre is not None:
        sql += " AND bimestre = %s"
        params.append(bimestre)
    sql += " ORDER BY fecha_publicacion DESC, id_material DESC"
    return consultar_todos(sql, tuple(params))


def buscar(id_material: int):
    return consultar_uno(f"SELECT {_COLUMNAS} FROM material_clase WHERE id_material = %s",
                         (id_material,))


def crear(id_carga: int, titulo: str, bimestre: int, descripcion, archivo_url) -> int:
    return insertar("""
        INSERT INTO material_clase (id_carga_academica, titulo, bimestre, descripcion, archivo_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_carga, titulo, bimestre, descripcion, archivo_url))


def actualizar(id_material: int, titulo: str, bimestre: int, descripcion, archivo_url) -> int:
    return ejecutar("""
        UPDATE material_clase
        SET titulo = %s, bimestre = %s, descripcion = %s, archivo_url = %s
        WHERE id_material = %s
    """, (titulo, bimestre, descripcion, archivo_url, id_material))


def eliminar(id_material: int) -> int:
    return ejecutar("DELETE FROM material_clase WHERE id_material = %s", (id_material,))
