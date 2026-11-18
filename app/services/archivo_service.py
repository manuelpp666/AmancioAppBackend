"""Archivos subidos: PDF, Word, Excel, PowerPoint, imágenes...

Cómo funciona:
1. La app envía el archivo en una petición multipart/form-data (campo "archivo").
2. `guardar()` revisa el tipo y el tamaño, lo guarda en la carpeta CARPETA_ARCHIVOS
   con un nombre aleatorio y crea su fila en la tabla `archivo`.
3. Cuando la API devuelve una tarea o entrega, `anidar()` agrega:
       "archivo": {"id_archivo", "nombre", "tipo", "tamano", "url"}
   `url` es un enlace firmado (con fecha de vencimiento) para abrirlo:
       GET /archivos/<id>?token=...
   Así el archivo se puede abrir en el navegador del celular sin enviar el JWT,
   y solo lo abre quien recibió el enlace de la API (alguien con permiso).

Para aceptar otro tipo de archivo, agrégalo en TIPOS_PERMITIDOS.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.datastructures import FileStorage

from app import config
from app.database import get_db
from app.errors import ApiError
from app.repositories import archivo_repository

log = logging.getLogger(__name__)

# Extensión → tipo (MIME) con el que se devuelve el archivo.
TIPOS_PERMITIDOS = {
    # Documentos
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
    # Imágenes
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".heic": "image/heic",
    # Comprimidos
    ".zip": "application/zip",
    ".rar": "application/vnd.rar",
}

# Estos tipos se muestran dentro del navegador; los demás se descargan.
_SE_VEN_EN_NAVEGADOR = ("application/pdf", "image/", "text/plain")


# --- Guardar ----------------------------------------------------------------------

def _extension(nombre: str) -> str:
    return os.path.splitext(nombre or "")[1].lower()


def _tamano(subido: FileStorage) -> int:
    """Bytes del archivo (se va al final del contenido y se vuelve al inicio)."""
    subido.stream.seek(0, os.SEEK_END)
    tamano = subido.stream.tell()
    subido.stream.seek(0)
    return tamano


def guardar(subido: FileStorage, id_usuario: int) -> dict:
    """Valida y guarda un archivo. NO hace commit: va en la transacción de quien lo llama.

    Devuelve {"id_archivo", "ruta"}. Si después la transacción falla, quien lo llamó
    debe llamar a `borrar_del_disco(guardado["ruta"])` para no dejar el archivo suelto.
    """
    nombre = os.path.basename((subido.filename or "").replace("\\", "/")).strip()
    extension = _extension(nombre)
    if not nombre:
        raise ApiError(400, "El archivo no tiene nombre")
    if extension not in TIPOS_PERMITIDOS:
        permitidos = ", ".join(sorted(e.lstrip(".") for e in TIPOS_PERMITIDOS))
        raise ApiError(400, f"Tipo de archivo no permitido. Se aceptan: {permitidos}")
    tamano = _tamano(subido)
    if tamano == 0:
        raise ApiError(400, "El archivo está vacío")
    if tamano > config.MAX_ARCHIVO_MB * 1024 * 1024:
        raise ApiError(413, f"El archivo es demasiado grande: máximo {config.MAX_ARCHIVO_MB} MB")

    # Nombre aleatorio en el disco: evita choques y que alguien adivine los archivos.
    nombre_guardado = uuid.uuid4().hex + extension
    ruta = os.path.join(config.CARPETA_ARCHIVOS, nombre_guardado)
    subido.save(ruta)
    try:
        id_archivo = archivo_repository.crear(id_usuario, nombre[-255:], nombre_guardado,
                                              TIPOS_PERMITIDOS[extension], tamano)
    except Exception:
        borrar_del_disco(ruta)
        raise
    return {"id_archivo": id_archivo, "ruta": ruta}


def borrar_del_disco(ruta: str | None) -> None:
    """Borra un archivo de la carpeta (si no existe, no pasa nada)."""
    if not ruta:
        return
    try:
        os.remove(ruta)
    except FileNotFoundError:
        pass
    except OSError as error:
        log.warning("No se pudo borrar el archivo %s: %s", ruta, error)


def eliminar(id_archivo: int | None) -> None:
    """Borra un archivo (fila y disco). Se usa DESPUÉS del commit, al reemplazarlo.
    Nunca lanza errores: si falla, solo queda un archivo sin usar."""
    if not id_archivo:
        return
    try:
        archivo = archivo_repository.buscar(id_archivo)
        if archivo is None:
            return
        archivo_repository.eliminar(id_archivo)
        get_db().commit()
        borrar_del_disco(os.path.join(config.CARPETA_ARCHIVOS, archivo["nombre_guardado"]))
    except Exception as error:     # noqa: BLE001
        log.warning("No se pudo eliminar el archivo %s: %s", id_archivo, error)


# --- Enlaces para abrir un archivo ---------------------------------------------------

def firmar(id_archivo: int) -> str:
    """Token que permite abrir ESE archivo durante HORAS_ENLACE_ARCHIVO horas."""
    vence = datetime.now(timezone.utc) + timedelta(hours=config.HORAS_ENLACE_ARCHIVO)
    return jwt.encode({"archivo": id_archivo, "exp": vence}, config.SECRET_KEY,
                      algorithm=config.JWT_ALGORITHM)


def url(id_archivo: int) -> str:
    """Ruta para abrir el archivo (la app le antepone la dirección del servidor)."""
    return f"/archivos/{id_archivo}?token={firmar(id_archivo)}"


def anidar(fila: dict, prefijo: str = "archivo_", clave: str = "archivo") -> dict:
    """Junta las columnas del archivo que trae una consulta en un solo objeto.

    {"archivo_id": 5, "archivo_nombre": "tarea.pdf", "archivo_tipo": ..., "archivo_tamano": ...}
      →  {"archivo": {"id_archivo": 5, "nombre": "tarea.pdf", "tipo": ..., "tamano": ..., "url": ...}}
    Si no hay archivo, queda "archivo": null.
    """
    id_archivo = fila.pop(f"{prefijo}id", None)
    nombre = fila.pop(f"{prefijo}nombre", None)
    tipo = fila.pop(f"{prefijo}tipo", None)
    tamano = fila.pop(f"{prefijo}tamano", None)
    fila[clave] = None if id_archivo is None else {
        "id_archivo": id_archivo, "nombre": nombre, "tipo": tipo, "tamano": tamano,
        "url": url(id_archivo),
    }
    return fila


def para_abrir(id_archivo: int, token: str | None) -> dict:
    """Comprueba el token del enlace y devuelve lo necesario para enviar el archivo."""
    if not token:
        raise ApiError(401, "Falta el token del enlace")
    try:
        datos = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM],
                           options={"require": ["exp", "archivo"]})
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "El enlace venció: vuelve a abrir la tarea para obtener uno nuevo")
    except jwt.InvalidTokenError:
        raise ApiError(401, "Enlace inválido")
    if datos["archivo"] != id_archivo:
        raise ApiError(401, "Enlace inválido")

    archivo = archivo_repository.buscar(id_archivo)
    ruta = archivo and os.path.join(config.CARPETA_ARCHIVOS, archivo["nombre_guardado"])
    if archivo is None or not os.path.isfile(ruta):
        raise ApiError(404, "Archivo no encontrado")
    return {
        "ruta": ruta,
        "nombre": archivo["nombre_original"],
        "tipo": archivo["tipo_mime"],
        "en_navegador": archivo["tipo_mime"].startswith(_SE_VEN_EN_NAVEGADOR),
    }
