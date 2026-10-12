"""Aula virtual (tareas y material de clase) y mensajería entre usuarios."""
from sqlalchemy import DECIMAL, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Tarea(Base):
    """Tarea o examen que el docente publica para un curso (su carga académica)."""
    __tablename__ = "tarea"

    id_tarea = Column(Integer, primary_key=True)
    id_carga_academica = Column(Integer, ForeignKey("carga_academica.id_carga_academica"))
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha_publicacion = Column(DateTime, server_default=func.now())
    fecha_entrega = Column(DateTime, nullable=True)         # fecha límite
    archivo_adjunto_url = Column(String(255), nullable=True)
    estado = Column(String(20), default="ACTIVO")
    tipo_evaluacion = Column(String(30), default="TAREA")   # TAREA, EXAMEN_PARCIAL, EXAMEN_BIMESTRAL
    bimestre = Column(Integer, nullable=False)              # 1 a 4
    peso = Column(Integer, default=0)                       # cuánto vale en el promedio

    # Entregas de los alumnos. Si se borra la tarea, se borran sus entregas.
    entregas = relationship("EntregaTarea", back_populates="tarea", cascade="all, delete-orphan")


class EntregaTarea(Base):
    """Lo que un alumno entrega para una tarea, y la nota que le pone el docente."""
    __tablename__ = "entrega_tarea"

    id_entrega = Column(Integer, primary_key=True)
    id_tarea = Column(Integer, ForeignKey("tarea.id_tarea"))
    id_alumno = Column(Integer, ForeignKey("alumno.id_alumno"))
    archivo_url = Column(String(255))
    comentario_alumno = Column(Text)
    fecha_envio = Column(DateTime, server_default=func.now(), onupdate=func.now())
    calificacion = Column(DECIMAL(4, 2))
    retroalimentacion_docente = Column(Text)

    tarea = relationship("Tarea", back_populates="entregas")
    alumno = relationship("Alumno")


class MaterialClase(Base):
    """Archivo o recurso que el docente comparte con el curso."""
    __tablename__ = "material_clase"

    id_material = Column(Integer, primary_key=True)
    id_carga_academica = Column(Integer, ForeignKey("carga_academica.id_carga_academica"))
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    archivo_url = Column(String(255), nullable=True)
    bimestre = Column(Integer, nullable=False)              # 1 a 4
    fecha_publicacion = Column(DateTime, server_default=func.now())


class Conversacion(Base):
    """Chat entre dos usuarios."""
    __tablename__ = "conversacion"

    id_conversacion = Column(Integer, primary_key=True)
    usuario1_id = Column(Integer, ForeignKey("usuario.id_usuario"))
    usuario2_id = Column(Integer, ForeignKey("usuario.id_usuario"))
    ultimo_mensaje = Column(Text)                           # para mostrar la vista previa
    fecha_actualizacion = Column(DateTime, server_default=func.now())


class Mensaje(Base):
    """Un mensaje dentro de una conversación."""
    __tablename__ = "mensaje"

    id_mensaje = Column(Integer, primary_key=True)
    id_conversacion = Column(Integer, ForeignKey("conversacion.id_conversacion"))
    remitente_id = Column(Integer, ForeignKey("usuario.id_usuario"))
    contenido = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)
    fecha_envio = Column(DateTime, server_default=func.now())
