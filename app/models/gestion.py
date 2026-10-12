"""Gestión académica: quién dicta qué curso, asistencia y notas."""
from sqlalchemy import CHAR, DECIMAL, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CargaAcademica(Base):
    """Asignación de un curso a un docente en una sección y año.
    Ej.: el docente Carlos dicta Matemática en 3ro "A" del 2026."""
    __tablename__ = "carga_academica"

    id_carga_academica = Column(Integer, primary_key=True)
    id_anio_escolar = Column(CHAR(6), ForeignKey("anio_escolar.id_anio_escolar"))
    id_seccion = Column(Integer, ForeignKey("seccion.id_seccion"))
    id_curso = Column(Integer, ForeignKey("curso.id_curso"))
    id_docente = Column(Integer, ForeignKey("docente.id_docente"))

    curso = relationship("Curso")
    docente = relationship("Docente")
    seccion = relationship("Seccion")
    anio_escolar = relationship("AnioEscolar")


class Asistencia(Base):
    """Asistencia de un alumno (por su matrícula) en un día."""
    __tablename__ = "asistencia"

    id_asistencia = Column(Integer, primary_key=True)
    id_matricula = Column(Integer, ForeignKey("matricula.id_matricula"))
    fecha = Column(Date, nullable=False)
    estado = Column(String(1), nullable=False)   # P = presente, T = tardanza, F = falta, J = justificada
    observacion = Column(String(150))


class Nota(Base):
    """Una nota de un alumno en un curso y bimestre."""
    __tablename__ = "nota"
    # Solo una nota de cada tipo por alumno, curso y bimestre (evita duplicados).
    __table_args__ = (
        UniqueConstraint("id_matricula", "id_curso", "bimestre", "tipo_nota",
                         name="uq_nota_alumno_curso_bim"),
    )

    id_nota = Column(Integer, primary_key=True)
    id_matricula = Column(Integer, ForeignKey("matricula.id_matricula"))
    id_curso = Column(Integer, ForeignKey("curso.id_curso"))
    bimestre = Column(Integer, nullable=False)              # 1 a 4
    tipo_nota = Column(String(20), default="PROMEDIO")
    valor = Column(DECIMAL(4, 2), nullable=False)           # de 0.00 a 20.00
    fecha_registro = Column(DateTime, server_default=func.now())


class ResumenNota(Base):
    """Libreta de un curso: las notas de los 4 bimestres en una sola fila."""
    __tablename__ = "resumen_nota"
    # Una sola fila por alumno y curso.
    __table_args__ = (
        UniqueConstraint("id_matricula", "id_curso", name="uq_resumen_alumno_curso"),
    )

    id_resumen_notas = Column(Integer, primary_key=True)
    id_matricula = Column(Integer, ForeignKey("matricula.id_matricula"))
    id_curso = Column(Integer, ForeignKey("curso.id_curso"))
    nota_bimestre1 = Column(DECIMAL(5, 2))
    nota_bimestre2 = Column(DECIMAL(5, 2))
    nota_bimestre3 = Column(DECIMAL(5, 2))
    nota_bimestre4 = Column(DECIMAL(5, 2))
    promedio_final = Column(DECIMAL(5, 2))
    estado_curso = Column(String(20), default="EN CURSO")


class CursoNotaAutomatica(Base):
    """Curso que sale en la libreta pero no se dicta: siempre lleva la misma nota (20)."""
    __tablename__ = "curso_nota_automatica"

    id_curso = Column(Integer, ForeignKey("curso.id_curso"), primary_key=True)
    id_grado = Column(Integer, ForeignKey("grado.id_grado"), primary_key=True)
    valor = Column(DECIMAL(4, 2), nullable=False, default=20)
