"""Interruptores globales del colegio (tabla pagina_configuracion)."""
from app.models.pagina_configuracion import PaginaConfiguracion

CLAVE_FORZAR_CAMBIO = "forzar_cambio_password_inicial"
CLAVE_EXIGIR_CORREO = "exigir_correo_primer_ingreso"


def _interruptor(db, clave: str) -> bool:
    """Si la clave no está configurada, se asume activada."""
    fila = db.query(PaginaConfiguracion).filter(PaginaConfiguracion.clave == clave).first()
    if not fila:
        return True
    return str(fila.valor).strip().lower() in ("1", "true", "si", "sí", "on")


def exigir_cambio_password(db) -> bool:
    return _interruptor(db, CLAVE_FORZAR_CAMBIO)


def exigir_correo(db) -> bool:
    return _interruptor(db, CLAVE_EXIGIR_CORREO)
