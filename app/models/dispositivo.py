"""Tabla `dispositivo_push`: el token de notificaciones de cada celular.

Cuando la app inicia sesión, envía el token que le da Firebase (FCM). Con ese
token, el servidor podrá enviar notificaciones push a ese celular.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class DispositivoPush(Base):
    __tablename__ = "dispositivo_push"

    id_dispositivo = Column(Integer, primary_key=True, autoincrement=True)
    # Dueño del celular. Si se borra el usuario, se borran sus dispositivos (CASCADE).
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                        nullable=False, index=True)
    # Cada token es único: si otra persona inicia sesión en el mismo celular,
    # el token pasa a ser de esa persona.
    token = Column(String(255), nullable=False, unique=True)
    plataforma = Column(String(20), nullable=False)          # "android" o "ios"
    activo = Column(Boolean, nullable=False, default=True)   # False = no enviarle notificaciones
    fecha_registro = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
