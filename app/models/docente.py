"""Tabla `docente`: datos del profesor."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Docente(Base):
    __tablename__ = "docente"

    id_docente = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), unique=True)  # su cuenta
    dni = Column(String(8), unique=True, index=True, nullable=False)
    nombres = Column(String(250), nullable=False)
    apellidos = Column(String(250), nullable=False)
    especialidad = Column(String(100))
    descripcion = Column(Text)
    telefono = Column(String(9))
    email = Column(String(100))
    url_perfil = Column(String(255))                              # foto de perfil
    visible_web = Column(Boolean, nullable=False, default=True)   # sale en la web pública

    usuario = relationship("Usuario", back_populates="docente")
