"""Tablas del personal no docente: administrador, auxiliar y psicólogo.

Las tres tienen la misma forma: datos personales + su cuenta (`id_usuario`).
"""
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Administrador(Base):
    __tablename__ = "administrador"

    id_admin = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), unique=True)
    dni = Column(String(8), unique=True, nullable=False)
    nombres = Column(String(250), nullable=False)
    apellidos = Column(String(250), nullable=False)
    telefono = Column(String(9))
    email = Column(String(100))
    url_perfil = Column(String(255), nullable=True)
    permisos = Column(JSON, nullable=True)   # lista de secciones que puede usar, ej. ["*"] = todas

    usuario = relationship("Usuario")


class Auxiliar(Base):
    __tablename__ = "auxiliar"

    id_auxiliar = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), unique=True)
    dni = Column(String(8), unique=True, nullable=False)
    nombres = Column(String(250), nullable=False)
    apellidos = Column(String(250), nullable=False)
    telefono = Column(String(9))
    email = Column(String(100))

    usuario = relationship("Usuario")


class Psicologo(Base):
    __tablename__ = "psicologo"

    id_psicologo = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), unique=True)
    dni = Column(String(8), unique=True, nullable=False)
    nombres = Column(String(250), nullable=False)
    apellidos = Column(String(250), nullable=False)
    telefono = Column(String(9))
    email = Column(String(100))

    usuario = relationship("Usuario")
