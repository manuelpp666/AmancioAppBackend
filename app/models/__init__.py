"""Modelos: cada clase representa una tabla de MySQL.

Se importan todos aquí para que SQLAlchemy conozca todas las tablas antes de
resolver las relaciones entre ellas (que se escriben por nombre, como "Alumno").

    usuario       cuentas de acceso (login) y su rol
    alumno        datos del alumno            familiar    su apoderado (uno por alumno)
    docente       datos del docente           personal    administrador, auxiliar, psicólogo
    academico     año escolar, bimestres, niveles, grados, secciones, áreas y cursos
    matricula     matrícula del alumno en un año y solicitudes de matrícula
    gestion       carga académica (qué docente dicta qué curso), asistencia y notas
    virtual       tareas, entregas, material de clase y mensajería
    dispositivo   tokens de notificaciones push de cada celular
"""
from app.models import (  # noqa: F401
    usuario, alumno, familiar, docente, personal,
    academico, matricula, gestion, virtual, dispositivo,
)
