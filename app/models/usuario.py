"""Tabla `usuario`: la cuenta con la que se inicia sesión."""
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)   # ej. ALU-12345678
    password_hash = Column(String(255), nullable=False)          # nunca la clave real
    rol = Column(Enum("ADMIN", "DOCENTE", "ALUMNO", "AUXILIAR", "PSICOLOGO"), nullable=False)
    activo = Column(Boolean, default=1)                          # False = no puede entrar
    # Lo usa el campus web para pedir un cambio de clave la primera vez.
    # La app lo pone en False cuando el usuario cambia su contraseña.
    debe_cambiar_password = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Ficha de la persona según su rol (uselist=False: es una sola, no una lista).
    alumno = relationship("Alumno", back_populates="usuario", uselist=False)
    docente = relationship("Docente", back_populates="usuario", uselist=False)
