"""Estructura académica del colegio.

    AnioEscolar ─┬─ Bimestre (4 por año)
                 └─ Seccion ── Grado ── Nivel (Primaria / Secundaria)
    Area ── Curso ── PlanEstudio (qué cursos lleva cada grado)
"""
from sqlalchemy import CHAR, Boolean, Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class AnioEscolar(Base):
    """Un año escolar, ej. "2026". Solo uno está activo a la vez."""
    __tablename__ = "anio_escolar"

    id_anio_escolar = Column(String(6), primary_key=True)    # ej. "2026"
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    activo = Column(Boolean, default=False)
    tipo = Column(String(20), default="REGULAR")             # REGULAR o VERANO
    inicio_inscripcion = Column(Date, nullable=True)         # periodo de matrícula
    fin_inscripcion = Column(Date, nullable=True)

    bimestres = relationship("Bimestre", order_by="Bimestre.numero")


class Bimestre(Base):
    """Fechas de inicio y fin de cada uno de los 4 bimestres de un año."""
    __tablename__ = "bimestre"
    # No puede haber dos "bimestre 1" en el mismo año.
    __table_args__ = (
        UniqueConstraint("id_anio_escolar", "numero", name="uq_bimestre_anio_numero"),
    )

    id_bimestre = Column(Integer, primary_key=True)
    id_anio_escolar = Column(String(6), ForeignKey("anio_escolar.id_anio_escolar"), nullable=False)
    numero = Column(Integer, nullable=False)          # 1, 2, 3 o 4
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)


class Nivel(Base):
    """Primaria o Secundaria."""
    __tablename__ = "nivel"

    id_nivel = Column(Integer, primary_key=True)
    nombre = Column(String(20), nullable=False)

    grados = relationship("Grado", back_populates="nivel", order_by="Grado.orden")


class Grado(Base):
    """Un grado dentro de un nivel, ej. "3ro" de Primaria."""
    __tablename__ = "grado"

    id_grado = Column(Integer, primary_key=True)
    id_nivel = Column(Integer, ForeignKey("nivel.id_nivel"))
    nombre = Column(String(20), nullable=False)
    orden = Column(Integer, nullable=False)           # para ordenarlos (1ro, 2do, ...)

    nivel = relationship("Nivel", back_populates="grados")
    planes_estudio = relationship("PlanEstudio", back_populates="grado")


class Seccion(Base):
    """Una sección de un grado en un año, ej. 3ro "A" del 2026."""
    __tablename__ = "seccion"

    id_seccion = Column(Integer, primary_key=True)
    id_grado = Column(Integer, ForeignKey("grado.id_grado"))
    id_anio_escolar = Column(CHAR(6), ForeignKey("anio_escolar.id_anio_escolar"), nullable=False)
    nombre = Column(String(30), nullable=False)       # ej. "A", "B", "Amarillo", "Única"
    vacantes = Column(Integer, default=30)

    grado = relationship("Grado")
    anio_escolar = relationship("AnioEscolar")


class Area(Base):
    """Área curricular, ej. Matemática, Comunicación."""
    __tablename__ = "area"

    id_area = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    # Posición del área en la libreta de notas (cambia según el nivel).
    # NULL = el área no existe en ese nivel.
    orden_primaria = Column(Integer)
    orden_secundaria = Column(Integer)


class Curso(Base):
    """Un curso que pertenece a un área, ej. Álgebra (área Matemática)."""
    __tablename__ = "curso"

    id_curso = Column(Integer, primary_key=True)
    id_area = Column(Integer, ForeignKey("area.id_area"))
    nombre = Column(String(100), nullable=False)
    minutos_semanales = Column(Integer, default=0)
    # Cursos del ciclo de verano
    es_verano = Column(Boolean, default=False)
    tipo_verano = Column(String(20), nullable=True)    # FIJO o TALLER
    grupo_verano = Column(String(20), nullable=True)   # ej. PRIM_1_2, SEC_1

    area = relationship("Area")


class PlanEstudio(Base):
    """Qué cursos lleva cada grado."""
    __tablename__ = "plan_estudio"

    id_plan_estudio = Column(Integer, primary_key=True)
    id_curso = Column(Integer, ForeignKey("curso.id_curso"))
    id_grado = Column(Integer, ForeignKey("grado.id_grado"))

    grado = relationship("Grado", back_populates="planes_estudio")
    curso = relationship("Curso")
