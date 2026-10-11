"""Tabla NUEVA del proyecto móvil: tokens de notificaciones push por dispositivo.

No existe en la base del campus web. Se crea con:
    flask --app run crear-tabla-dispositivos
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class DispositivoPush(Base):
    __tablename__ = "dispositivo_push"

    id_dispositivo = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                        nullable=False, index=True)
    # Un mismo token pertenece a un solo usuario a la vez: si otra persona inicia
    # sesión en el mismo teléfono, el token se reasigna.
    token = Column(String(255), nullable=False, unique=True)
    plataforma = Column(String(20), nullable=False)          # "android" | "ios"
    activo = Column(Boolean, nullable=False, default=True)
    fecha_registro = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
