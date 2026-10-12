"""Tabla `familiar`: el apoderado del alumno (padre, madre u otro).

Relación uno a muchos: un familiar puede tener varios hijos en el colegio,
pero cada alumno tiene un solo familiar (columna `alumno.id_familiar`).
El correo y el teléfono de contacto del alumno se guardan aquí.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Familiar(Base):
    __tablename__ = "familiar"

    id_familiar = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True)
    nombres = Column(String(250))
    apellidos = Column(String(250))
    telefono = Column(String(9))
    email = Column(String(150))
    direccion = Column(String(300))

    # Lista de alumnos de este familiar: familiar.hijos
    hijos = relationship("Alumno", back_populates="familiar")
