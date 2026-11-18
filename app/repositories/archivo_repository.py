"""Consultas SQL de la tabla `archivo` (archivos subidos: PDF, Word, imágenes...).

El archivo en sí está en la carpeta CARPETA_ARCHIVOS del servidor con el nombre
`nombre_guardado` (aleatorio); aquí se guarda su nombre original, tipo y tamaño.
"""
from app.database import consultar_uno, ejecutar, insertar


def crear(id_usuario: int, nombre_original: str, nombre_guardado: str, tipo_mime: str,
          tamano_bytes: int) -> int:
    return insertar("""
        INSERT INTO archivo (id_usuario, nombre_original, nombre_guardado, tipo_mime, tamano_bytes)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_usuario, nombre_original, nombre_guardado, tipo_mime, tamano_bytes))


def buscar(id_archivo: int):
    return consultar_uno("""
        SELECT id_archivo, id_usuario, nombre_original, nombre_guardado, tipo_mime, tamano_bytes
        FROM archivo
        WHERE id_archivo = %s
    """, (id_archivo,))


def eliminar(id_archivo: int) -> int:
    return ejecutar("DELETE FROM archivo WHERE id_archivo = %s", (id_archivo,))
