"""Importar todos los modelos aquí garantiza que SQLAlchemy conozca todas las
tablas antes de resolver las relaciones (que se declaran con nombres de texto)."""
from app.models import (  # noqa: F401
    usuario, alumno, docente, familiar, relacion_familiar, personal,
    seguridad, pagina_configuracion, academico, matricula, horario,
    gestion, conducta, virtual, dispositivo,
)
