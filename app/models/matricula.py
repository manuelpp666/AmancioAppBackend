"""Matrícula: inscripción de un alumno en un grado/sección durante un año escolar."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Matricula(Base):
    """Un alumno matriculado en un año. Las notas y la asistencia cuelgan de aquí."""
    __tablename__ = "matricula"

    id_matricula = Column(Integer, primary_key=True, index=True)
    id_anio_escolar = Column(String(6), ForeignKey("anio_escolar.id_anio_escolar"))
    id_alumno = Column(Integer, ForeignKey("alumno.id_alumno"))
    id_grado = Column(Integer, ForeignKey("grado.id_grado"))
    id_seccion = Column(Integer, ForeignKey("seccion.id_seccion"), nullable=True)
    fecha_matricula = Column(DateTime, default=func.now())
    estado = Column(String(20), default="MATRICULADO")
    tipo_matricula = Column(String(20), default="REGULAR")
    condicion = Column(String(20), nullable=True, default="NORMAL")   # NORMAL, CONDICIONADA, REPITE

    alumno = relationship("Alumno")
    anio_escolar = relationship("AnioEscolar")
    grado = relationship("Grado")
    seccion = relationship("Seccion")


class SolicitudMatricula(Base):
    """Pedido de un alumno para matricularse el año siguiente; el admin la aprueba o rechaza."""
    __tablename__ = "solicitud_matricula"

    id_solicitud_matricula = Column(Integer, primary_key=True, index=True)
    id_alumno = Column(Integer, ForeignKey("alumno.id_alumno"), nullable=False)
    id_anio_escolar_origen = Column(String(6), nullable=True)
    anio_destino = Column(String(6), nullable=False)
    grado_destino = Column(String(50), nullable=True)
    comentario = Column(Text, nullable=True)
    estado = Column(String(20), default="PENDIENTE")   # PENDIENTE, APROBADA, RECHAZADA
    respuesta_admin = Column(Text, nullable=True)
    fecha_solicitud = Column(DateTime, default=func.now())

    alumno = relationship("Alumno")
