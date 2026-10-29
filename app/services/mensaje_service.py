"""Reglas de la mensajería interna (chat entre dos usuarios).

¿Con quién puede escribir cada uno? (sus "contactos")
    ALUMNO     los docentes de su sección, los auxiliares y los psicólogos
    DOCENTE    los alumnos de sus secciones y todo el personal
    AUXILIAR, PSICOLOGO, ADMIN   cualquier usuario activo

Para EMPEZAR una conversación el otro debe ser tu contacto (si no, 403). Una vez
creada, cualquiera de los dos puede responder. Nadie más puede leerla (403).
Cada mensaje nuevo crea una notificación para el otro usuario.
"""
from app.database import get_db
from app.errors import ApiError
from app.repositories import mensaje_repository, perfil_repository
from app.services import academico_service, cursos_service, notificacion_service
from app.utils import entero, texto

MAXIMO_CARACTERES = 2000
_VISTA_PREVIA = 100          # caracteres del último mensaje que se ven en la lista de chats
PERSONAL = ("ADMIN", "AUXILIAR", "PSICOLOGO", "DOCENTE")


# --- Ayudas -----------------------------------------------------------------------

def _conversacion_mia(usuario: dict, id_conversacion: int) -> dict:
    """La conversación, comprobando que el usuario participa en ella (404 / 403)."""
    conversacion = mensaje_repository.buscar_conversacion(id_conversacion)
    if conversacion is None:
        raise ApiError(404, "Conversación no encontrada")
    if usuario["id"] not in (conversacion["usuario1_id"], conversacion["usuario2_id"]):
        raise ApiError(403, "No participas en esta conversación")
    return conversacion


def _otro(conversacion: dict, id_usuario: int) -> int:
    """El id del otro participante."""
    if conversacion["usuario1_id"] == id_usuario:
        return conversacion["usuario2_id"]
    return conversacion["usuario1_id"]


def _guardar_mensaje(usuario: dict, id_conversacion: int, id_destino: int, contenido: str) -> int:
    """Inserta el mensaje, actualiza la conversación y avisa al otro.
    NO hace commit: lo hace quien la llama (todo va en una transacción)."""
    id_mensaje = mensaje_repository.crear_mensaje(id_conversacion, usuario["id"], contenido)
    mensaje_repository.actualizar_ultimo(id_conversacion, contenido[:_VISTA_PREVIA])
    remitente = mensaje_repository.usuario_con_nombre(usuario["id"])
    notificacion_service.notificar([id_destino], "MENSAJE", f"Mensaje de {remitente['nombre']}",
                                   contenido[:_VISTA_PREVIA], id_conversacion)
    return id_mensaje


# --- Casos de uso -------------------------------------------------------------------

def contactos(usuario: dict) -> list:
    """Con quién puede iniciar una conversación el usuario (según su rol)."""
    anio = academico_service.anio_activo()["id_anio_escolar"]

    if usuario["rol"] == "ALUMNO":
        matricula = cursos_service.matricula_actual(usuario["id"])
        docentes = (mensaje_repository.docentes_de_seccion(matricula["id_seccion"], anio)
                    if matricula and matricula["id_seccion"] else [])
        return docentes + mensaje_repository.personal(("AUXILIAR", "PSICOLOGO"), usuario["id"])

    if usuario["rol"] == "DOCENTE":
        docente = perfil_repository.docente_por_usuario(usuario["id"])
        alumnos = mensaje_repository.alumnos_de_docente(docente["id_docente"], anio) if docente else []
        return mensaje_repository.personal(PERSONAL, usuario["id"]) + alumnos

    # AUXILIAR, PSICOLOGO y ADMIN pueden escribir a cualquiera.
    return mensaje_repository.personal(PERSONAL + ("ALUMNO",), usuario["id"])


def conversaciones(usuario: dict) -> list:
    return mensaje_repository.conversaciones_de(usuario["id"])


def iniciar(usuario: dict, datos: dict) -> tuple[dict, int]:
    """Escribe a un contacto. Si ya tenían una conversación, se usa esa (200);
    si no, se crea (201). Todo en una transacción."""
    id_destino = entero(datos, "id_usuario", minimo=1, maximo=2_000_000_000)
    contenido = texto(datos, "contenido", minimo=1, maximo=MAXIMO_CARACTERES)
    if id_destino == usuario["id"]:
        raise ApiError(400, "No puedes enviarte mensajes a ti mismo")
    destino = mensaje_repository.usuario_con_nombre(id_destino)
    if destino is None or not destino["activo"]:
        raise ApiError(404, "Usuario no encontrado")
    if id_destino not in {c["id_usuario"] for c in contactos(usuario)}:
        raise ApiError(403, "No puedes iniciar una conversación con este usuario")

    existente = mensaje_repository.conversacion_entre(usuario["id"], id_destino)

    db = get_db()
    try:
        if existente is None:
            id_conversacion = mensaje_repository.crear_conversacion(usuario["id"], id_destino)
            codigo = 201
        else:
            id_conversacion = existente["id_conversacion"]
            codigo = 200
        id_mensaje = _guardar_mensaje(usuario, id_conversacion, id_destino, contenido)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Mensaje enviado", "id_conversacion": id_conversacion,
            "id_mensaje": id_mensaje}, codigo


def ver(usuario: dict, id_conversacion: int) -> dict:
    """Los mensajes de una conversación (solo para sus dos participantes)."""
    conversacion = _conversacion_mia(usuario, id_conversacion)
    contacto = mensaje_repository.usuario_con_nombre(_otro(conversacion, usuario["id"]))
    mensajes = mensaje_repository.mensajes_de(id_conversacion)
    for m in mensajes:
        m["mio"] = m["remitente_id"] == usuario["id"]      # para dibujar la burbuja a la derecha
    return {"id_conversacion": id_conversacion,
            "contacto": {"id_usuario": contacto["id_usuario"], "nombre": contacto["nombre"],
                         "rol": contacto["rol"]},
            "mensajes": mensajes}


def enviar(usuario: dict, id_conversacion: int, datos: dict) -> dict:
    """Responde en una conversación existente."""
    contenido = texto(datos, "contenido", minimo=1, maximo=MAXIMO_CARACTERES)
    conversacion = _conversacion_mia(usuario, id_conversacion)

    db = get_db()
    try:
        id_mensaje = _guardar_mensaje(usuario, id_conversacion, _otro(conversacion, usuario["id"]),
                                      contenido)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Mensaje enviado", "id_conversacion": id_conversacion, "id_mensaje": id_mensaje}


def marcar_leidos(usuario: dict, id_conversacion: int) -> dict:
    _conversacion_mia(usuario, id_conversacion)

    db = get_db()
    try:
        marcados = mensaje_repository.marcar_leidos(id_conversacion, usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Mensajes leídos", "marcados": marcados}
