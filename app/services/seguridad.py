"""Freno a la prueba de contraseñas y registro de cada intento de acceso.

El contador vive en la base de datos (tabla intento_acceso) y no en memoria:
con varios procesos o reinicios, un contador en memoria se borraría solo.
Si algo falla aquí (tabla ausente, base saturada) se deja pasar: es preferible
quedarse sin freno un rato a que nadie pueda entrar.
"""
from datetime import datetime, timedelta

from flask import request
from sqlalchemy import desc

from app.models.seguridad import IntentoAcceso

VENTANA_MINUTOS = 15
MAX_FALLOS_USUARIO = 5     # tanteo contra una cuenta concreta
MAX_FALLOS_IP = 20         # barrido desde un mismo sitio contra muchas cuentas


def ip_de_la_peticion() -> str | None:
    """IP del cliente. Detrás de un proxy (Render) viaja en X-Forwarded-For."""
    reenviada = request.headers.get("X-Forwarded-For")
    if reenviada:
        primera = reenviada.split(",")[0].strip()
        if primera:
            return primera[:45]
    return (request.remote_addr or None)


def _restante(primer_fallo: datetime | None) -> int:
    if not primer_fallo:
        return VENTANA_MINUTOS * 60
    fin = primer_fallo + timedelta(minutes=VENTANA_MINUTOS)
    return max(1, int((fin - datetime.now()).total_seconds()))


def _calcular_bloqueo(db, username: str, ip: str | None) -> int:
    desde = datetime.now() - timedelta(minutes=VENTANA_MINUTOS)
    # Los fallos se cuentan desde el último acierto: quien entra bien reinicia el contador.
    ultimo_ok = (db.query(IntentoAcceso.fecha)
                 .filter(IntentoAcceso.username == username, IntentoAcceso.exito.is_(True),
                         IntentoAcceso.fecha >= desde)
                 .order_by(desc(IntentoAcceso.fecha)).first())
    corte = max(desde, ultimo_ok[0]) if ultimo_ok else desde

    fallos_usuario = (db.query(IntentoAcceso.fecha)
                      .filter(IntentoAcceso.username == username, IntentoAcceso.exito.is_(False),
                              IntentoAcceso.motivo != "BLOQUEADO", IntentoAcceso.fecha >= corte))
    if fallos_usuario.count() >= MAX_FALLOS_USUARIO:
        fila = fallos_usuario.order_by(IntentoAcceso.fecha).first()
        return _restante(fila[0] if fila else None)

    if ip:
        fallos_ip = (db.query(IntentoAcceso.fecha)
                     .filter(IntentoAcceso.ip == ip, IntentoAcceso.exito.is_(False),
                             IntentoAcceso.motivo != "BLOQUEADO", IntentoAcceso.fecha >= desde))
        if fallos_ip.count() >= MAX_FALLOS_IP:
            fila = fallos_ip.order_by(IntentoAcceso.fecha).first()
            return _restante(fila[0] if fila else None)
    return 0


def segundos_de_bloqueo(db, username: str, ip: str | None) -> int:
    """Segundos que faltan para poder reintentar. 0 = puede pasar."""
    try:
        return _calcular_bloqueo(db, username, ip)
    except Exception as e:  # noqa: BLE001
        print(f"[SEGURIDAD][WARN] No se pudo comprobar el bloqueo, se deja pasar: {e}")
        db.rollback()
        return 0


def anotar(db, username: str, exito: bool, motivo: str | None = None,
           id_usuario: int | None = None, rol: str | None = None) -> None:
    """Deja constancia del intento. Nunca interrumpe el login."""
    try:
        db.add(IntentoAcceso(
            username=(username or "")[:50], id_usuario=id_usuario, rol=rol,
            exito=exito, motivo=motivo, ip=ip_de_la_peticion(),
            user_agent=(request.headers.get("User-Agent") or "")[:255] or None,
        ))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
