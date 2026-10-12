"""Tabla `alumno`: datos personales del estudiante."""
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Alumno(Base):
    __tablename__ = "alumno"

    id_alumno = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), unique=True)  # su cuenta

    # Datos personales
    dni = Column(String(8), unique=True)
    nombres = Column(String(250), nullable=False)
    apellidos = Column(String(250), nullable=False)
    fecha_nacimiento = Column(Date)
    genero = Column(String(1))                    # "M" o "F"
    direccion = Column(String(300))
    enfermedad = Column(String(150))              # datos médicos
    talla_polo = Column(String(5))
    colegio_procedencia = Column(String(100))

    # Datos de admisión (los llena el campus web)
    id_grado_ingreso = Column(Integer, ForeignKey("grado.id_grado"), nullable=True)
    relacion_fraternal = Column(Boolean, default=False)   # tiene hermanos en el colegio
    estado_ingreso = Column(String(20), default="POSTULANTE")   # ej. POSTULANTE, ESTUDIANTE
    motivo_rechazo = Column(Text, nullable=True)
    doc_dni_menor = Column(String(500), nullable=True)            # URLs de documentos
    doc_dni_apoderado = Column(String(500), nullable=True)
    doc_fum = Column(String(500), nullable=True)                  # Ficha Única de Matrícula
    doc_certificado_estudios = Column(String(500), nullable=True)

    # Su familiar: cada alumno tiene UNO; un familiar puede tener varios hijos.
    id_familiar = Column(Integer, ForeignKey("familiar.id_familiar"), nullable=True)

    # Relaciones: permiten escribir alumno.usuario, alumno.familiar, etc.
    usuario = relationship("Usuario", back_populates="alumno")
    grado_ingreso = relationship("Grado")
    familiar = relationship("Familiar", back_populates="hijos")
