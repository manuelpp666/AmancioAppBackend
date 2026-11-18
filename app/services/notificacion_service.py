"""Reglas de las notificaciones.

Cómo se crea una notificación:
1. Un service hace algo que le interesa a alguien (el docente publica una tarea,
   el psicólogo programa una cita...) y llama a `notificar(...)` ANTES de su commit.
   Así la notificación es parte de la misma transacción: si la operación se
   deshace (rollback), la notificación también.
2. Si la petición terminó bien, después de responder se envía el aviso push al
   celular (ver `enviar_pendientes`, que llama app/__init__.py).

Los tipos de notificación que manda el sistema están en TIPOS (abajo).

Cada usuario puede SILENCIAR o LIMITAR las notificaciones push (ver "Preferencias"):
silenciarlas todas, pausarlas unas horas, elegir qué tipos recibir y un horario
"no molestar". Las preferencias solo afectan a lo que llega al celular: el aviso
siempre se guarda y se ve en la bandeja (GET /notificaciones).
"""
import logging
from datetime import datetime, time, timedelta

from flask import g

from app import config, push, tiempo_real
from app.database import get_db
from app.errors import ApiError
from app.repositories import (dispositivo_repository, mensaje_repository, notificacion_repository,
                              preferencia_repository)
from app.utils import hora_texto

log = logging.getLogger(__name__)

TODOS_LOS_ROLES = ("ALUMNO", "DOCENTE", "AUXILIAR", "PSICOLOGO", "ADMIN")

# Notificaciones que manda el sistema: quién las recibe y cuándo.
# Para agregar un tipo nuevo:
#   1. Agrégalo aquí (nombre, descripción y qué roles lo pueden recibir).
#   2. Llama a notificar(...) con ese tipo desde el service donde ocurre.
#   3. En la app, dale un ícono y una pantalla en src/config/notificaciones.js.
TIPOS = {
    "TAREA": {"nombre": "Tareas nuevas", "roles": ("ALUMNO",),
              "descripcion": "Cuando un docente publica una tarea en uno de tus cursos."},
    "CALIFICACION": {"nombre": "Tareas calificadas", "roles": ("ALUMNO",),
                     "descripcion": "Cuando el docente califica tu entrega."},
    "CLASE": {"nombre": "Clases virtuales", "roles": ("ALUMNO",),
              "descripcion": "Cuando se programa una clase en línea de tu curso."},
    "LIBRETA": {"nombre": "Libreta de notas", "roles": ("ALUMNO",),
                "descripcion": "Cuando el docente cierra el bimestre y tus notas pasan a la libreta."},
    "CITA": {"nombre": "Citas de psicología", "roles": ("ALUMNO",),
             "descripcion": "Cuando psicología programa, reprograma o cancela tu cita."},
    "CONDUCTA": {"nombre": "Reportes de conducta", "roles": ("ALUMNO",),
                 "descripcion": "Cuando se registra un reporte de conducta a tu nombre."},
    "MENSAJE": {"nombre": "Mensajes", "roles": TODOS_LOS_ROLES,
                "descripcion": "Cuando alguien te escribe por la mensajería."},
}

# Opciones de "pausar por un tiempo" que ofrece la app (en horas). El máximo es una semana.
OPCIONES_PAUSA_HORAS = (1, 8, 24)
MAXIMO_PAUSA_HORAS = 24 * 7


# --- Crear notificaciones (las usan los otros services) --------------------------

def notificar(id_usuarios: list, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    """Guarda la misma notificación para varios usuarios. NO hace commit: va dentro de la
    transacción del service que la llama. Devuelve cuántas creó.

    Un aviso es algo secundario: si no se puede guardar, se anota en el log y la operación
    principal (publicar la tarea, calificar...) sigue normalmente."""
    ids_notificacion = {}       # id_usuario → id de SU notificación
    for id_usuario in dict.fromkeys(id_usuarios):          # sin repetidos
        if id_usuario is None:
            continue
        try:
            ids_notificacion[id_usuario] = notificacion_repository.crear(
                id_usuario, tipo, titulo, mensaje[:300], id_referencia)
        except Exception as error:
            log.warning("No se pudo crear la notificación para el usuario %s: %s", id_usuario, error)

    if ids_notificacion:
        # Se anota para enviar el push al final de la petición (solo si terminó bien).
        g.setdefault("push_pendientes", []).append({
            "ids_notificacion": ids_notificacion, "titulo": titulo, "mensaje": mensaje,
            "tipo": tipo, "id_referencia": id_referencia,
        })
    return len(ids_notificacion)


def notificar_seccion(carga: dict, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    """Avisa a todos los alumnos de la sección de un curso."""
    try:
        alumnos = notificacion_repository.usuarios_de_seccion(carga["id_seccion"], carga["anio"])
    except Exception as error:
        log.warning("No se pudo obtener los alumnos de la sección para avisarles: %s", error)
        return 0
    return notificar(alumnos, tipo, titulo, mensaje, id_referencia)


def notificar_alumno(id_alumno: int, tipo: str, titulo: str, mensaje: str, id_referencia=None) -> int:
    """Avisa al usuario de un alumno."""
    try:
        id_usuario = notificacion_repository.usuario_de_alumno(id_alumno)
    except Exception as error:
        log.warning("No se pudo obtener el usuario del alumno %s: %s", id_alumno, error)
        return 0
    return notificar([id_usuario], tipo, titulo, mensaje, id_referencia)


def enviar_pendientes() -> None:
    """Envía los avisos anotados durante la petición (ya se hizo el commit), por dos vías:

    1. WebSocket (siempre, a todos): la app abierta lo recibe al instante, actualiza la
       lista y los globos, y muestra la notificación en el celular si `mostrar` es true.
       Funciona en local sin internet y sin development build (ver app/tiempo_real.py).
    2. Push de Expo (solo con PUSH_ACTIVO=1 y a quien no lo silenció): llega aunque la
       app esté cerrada. Necesita internet y una development build.

    Cada celular recibe en "data": el tipo, el id_referencia (para abrir la pantalla
    relacionada) y el id de SU notificación (para marcarla como leída al tocarla).
    Nunca lanza errores: la notificación ya está guardada en la base."""
    for aviso in g.pop("push_pendientes", []):
        try:
            todos = aviso["ids_notificacion"]                     # id_usuario → id_notificacion
            # Solo a quienes no silenciaron este tipo de aviso (ver "Preferencias").
            reciben = _quienes_reciben(list(todos), aviso["tipo"])
            dispositivos = (dispositivo_repository.dispositivos_activos([i for i in todos if i in reciben])
                            if config.PUSH_ACTIVO and reciben else [])
            con_push = {d["id_usuario"] for d in dispositivos}

            # 1. WebSocket: cada usuario recibe SU notificación.
            for id_usuario, id_notificacion in todos.items():
                tiempo_real.emitir([id_usuario], "notificacion", {
                    "id_notificacion": id_notificacion, "tipo": aviso["tipo"],
                    "titulo": aviso["titulo"], "mensaje": aviso["mensaje"],
                    "id_referencia": aviso["id_referencia"],
                    "mostrar": id_usuario in reciben,       # no la silenció
                    "push_enviado": id_usuario in con_push,  # además le llega como push
                })

            # 2. Push al celular.
            push.enviar_mensajes([
                push.armar_mensaje(disp["token"], aviso["titulo"], aviso["mensaje"], {
                    "tipo": aviso["tipo"],
                    "id_referencia": aviso["id_referencia"],
                    "id_notificacion": todos.get(disp["id_usuario"]),
                })
                for disp in dispositivos
            ])
        except Exception as error:
            log.warning("No se pudo enviar el aviso: %s", error)


# --- Bandeja del usuario -----------------------------------------------------------

def mis_notificaciones(usuario: dict, solo_no_leidas: bool = False) -> dict:
    return {
        "no_leidas": notificacion_repository.contar_no_leidas(usuario["id"]),
        "notificaciones": notificacion_repository.de_usuario(usuario["id"], solo_no_leidas),
    }


def contadores(usuario: dict) -> dict:
    """Mensajes y avisos sin leer (consulta liviana, para los globos de la barra de menú)."""
    return {
        "mensajes_no_leidos": mensaje_repository.no_leidos_total(usuario["id"]),
        "notificaciones_no_leidas": notificacion_repository.contar_no_leidas(usuario["id"]),
    }


def marcar_leida(usuario: dict, id_notificacion: int) -> dict:
    notificacion = notificacion_repository.buscar(id_notificacion)
    if notificacion is None:
        raise ApiError(404, "Notificación no encontrada")
    if notificacion["id_usuario"] != usuario["id"]:
        raise ApiError(403, "Esa notificación no es tuya")

    db = get_db()
    try:
        notificacion_repository.marcar_leida(id_notificacion)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Notificación leída"}


def marcar_todas(usuario: dict) -> dict:
    db = get_db()
    try:
        marcadas = notificacion_repository.marcar_todas(usuario["id"])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Notificaciones leídas", "marcadas": marcadas}


# --- Preferencias: silenciar o limitar las notificaciones push ------------------------
#
#   silenciar_todo        no llega ninguna notificación al celular
#   pausado_hasta         silenciadas hasta esa hora ("pausar 8 horas")
#   tipos_silenciados     los tipos que el usuario apagó (ej. CLASE y MENSAJE)
#   no_molestar           todos los días entre "desde" y "hasta" (ej. 22:00 a 07:00)

def _minutos(valor) -> int | None:
    """Hora de MySQL (timedelta) o time → minutos desde las 00:00."""
    if valor is None:
        return None
    if isinstance(valor, timedelta):
        return int(valor.total_seconds()) // 60
    return valor.hour * 60 + valor.minute


def _en_no_molestar(pref: dict, ahora: datetime) -> bool:
    desde, hasta = _minutos(pref.get("no_molestar_desde")), _minutos(pref.get("no_molestar_hasta"))
    if desde is None or hasta is None or desde == hasta:
        return False
    actual = ahora.hour * 60 + ahora.minute
    if desde < hasta:                       # mismo día, ej. 13:00 a 15:00
        return desde <= actual < hasta
    return actual >= desde or actual < hasta  # cruza la medianoche, ej. 22:00 a 07:00


def _recibe_push(pref: dict | None, tipo: str, ahora: datetime) -> bool:
    """¿Le llega al celular una notificación de este tipo, ahora? (sin fila = recibe todo)."""
    if pref is None:
        return True
    if pref["silenciar_todo"]:
        return False
    if pref["pausado_hasta"] is not None and ahora < pref["pausado_hasta"]:
        return False
    if tipo in _tipos_silenciados(pref):
        return False
    return not _en_no_molestar(pref, ahora)


def _tipos_silenciados(pref: dict | None) -> set:
    if not pref or not pref["tipos_silenciados"]:
        return set()
    return {t for t in pref["tipos_silenciados"].split(",") if t}


def _quienes_reciben(id_usuarios: list, tipo: str) -> set:
    """De esos usuarios, los que SÍ reciben el push de este tipo ahora."""
    preferencias = {p["id_usuario"]: p for p in preferencia_repository.de_usuarios(id_usuarios)}
    ahora = datetime.now()
    return {i for i in id_usuarios if _recibe_push(preferencias.get(i), tipo, ahora)}


def preferencias(usuario: dict) -> dict:
    """Las preferencias del usuario, con los tipos de aviso que le pueden llegar según su rol."""
    pref = preferencia_repository.buscar(usuario["id"])
    ahora = datetime.now()
    silenciados = _tipos_silenciados(pref)
    pausado = pref and pref["pausado_hasta"]
    hay_no_molestar = bool(pref and pref["no_molestar_desde"] is not None and pref["no_molestar_hasta"] is not None)
    return {
        "silenciar_todo": bool(pref and pref["silenciar_todo"]),
        "pausado_hasta": pausado if pausado and pausado > ahora else None,
        "no_molestar": {"desde": hora_texto(pref["no_molestar_desde"]),
                        "hasta": hora_texto(pref["no_molestar_hasta"])} if hay_no_molestar else None,
        "tipos": [{"tipo": tipo, "nombre": info["nombre"], "descripcion": info["descripcion"],
                   "activo": tipo not in silenciados}
                  for tipo, info in TIPOS.items() if usuario["rol"] in info["roles"]],
        "opciones_pausa_horas": list(OPCIONES_PAUSA_HORAS),
        # ¿Le llegaría AHORA un mensaje? (para mostrar "Silenciadas" en la app)
        "recibe_ahora": _recibe_push(pref, "MENSAJE", ahora) if pref else True,
    }


def _hora(datos: dict, campo: str):
    """Lee una hora "HH:MM" (o null). Devuelve time o None."""
    valor = datos.get(campo)
    if valor in (None, ""):
        return None
    try:
        horas, minutos = str(valor).split(":")
        return time(int(horas), int(minutos))
    except ValueError:
        raise ApiError(400, f"El campo '{campo}' debe tener el formato HH:MM (24 horas)")


def guardar_preferencias(usuario: dict, datos: dict) -> dict:
    """Guarda las preferencias. Todos los campos son opcionales: lo que no se envía
    se queda como estaba.

        {"silenciar_todo": false,
         "tipos_silenciados": ["CLASE"],
         "no_molestar_desde": "22:00", "no_molestar_hasta": "07:00",   (null = sin horario)
         "pausar_horas": 8}                                              (0 = quitar la pausa)
    """
    actual = preferencia_repository.buscar(usuario["id"]) or {
        "silenciar_todo": 0, "pausado_hasta": None, "tipos_silenciados": "",
        "no_molestar_desde": None, "no_molestar_hasta": None,
    }

    silenciar_todo = bool(actual["silenciar_todo"])
    if "silenciar_todo" in datos:
        if not isinstance(datos["silenciar_todo"], bool):
            raise ApiError(400, "El campo 'silenciar_todo' debe ser true o false")
        silenciar_todo = datos["silenciar_todo"]

    tipos = _tipos_silenciados(actual)
    if "tipos_silenciados" in datos:
        lista = datos["tipos_silenciados"]
        if not isinstance(lista, list) or any(t not in TIPOS for t in lista):
            raise ApiError(400, "tipos_silenciados debe ser una lista con: " + ", ".join(TIPOS))
        tipos = set(lista)

    desde, hasta = actual["no_molestar_desde"], actual["no_molestar_hasta"]
    if "no_molestar_desde" in datos or "no_molestar_hasta" in datos:
        desde, hasta = _hora(datos, "no_molestar_desde"), _hora(datos, "no_molestar_hasta")
        if (desde is None) != (hasta is None):
            raise ApiError(400, "Indica las dos horas del horario 'no molestar' (o ninguna)")
        if desde is not None and desde == hasta:
            raise ApiError(400, "La hora de inicio y la de fin no pueden ser iguales")

    pausado_hasta = actual["pausado_hasta"]
    if "pausar_horas" in datos:
        horas = datos["pausar_horas"]
        if not isinstance(horas, int) or isinstance(horas, bool) or not 0 <= horas <= MAXIMO_PAUSA_HORAS:
            raise ApiError(400, f"pausar_horas debe ser un número entre 0 y {MAXIMO_PAUSA_HORAS}")
        pausado_hasta = datetime.now().replace(microsecond=0) + timedelta(hours=horas) if horas else None

    # Se guardan en el orden de TIPOS para que siempre se vea igual.
    tipos_texto = ",".join(t for t in TIPOS if t in tipos)

    db = get_db()
    try:
        preferencia_repository.guardar(usuario["id"], silenciar_todo, pausado_hasta, tipos_texto, desde, hasta)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Preferencias guardadas", **preferencias(usuario)}
