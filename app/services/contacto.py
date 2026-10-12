"""Datos de contacto (correo y teléfono) de cualquier usuario.

¿Dónde se guardan?
- Docente, administrador, auxiliar y psicólogo: en su propia ficha.
- Alumno: la tabla `alumno` no tiene correo ni teléfono; se usan los de su
  familiar, que es quien recibe los avisos del colegio.
"""
from app.models.alumno import Alumno
from app.models.docente import Docente
from app.models.familiar import Familiar
from app.models.personal import Administrador, Auxiliar, Psicologo

# Qué tabla tiene la ficha de cada rol (el alumno se trata aparte).
FICHA_POR_ROL = {
    "ALUMNO": Alumno,
    "DOCENTE": Docente,
    "ADMIN": Administrador,
    "AUXILIAR": Auxiliar,
    "PSICOLOGO": Psicologo,
}


def ficha_de(db, usuario):
    """Ficha de la persona según su rol (un Alumno, un Docente...), o None si no tiene."""
    modelo = FICHA_POR_ROL.get(usuario.rol)
    if modelo is None:
        return None
    return db.query(modelo).filter(modelo.id_usuario == usuario.id_usuario).first()


def _donde_esta_el_contacto(db, usuario):
    """Registro que guarda el correo y el teléfono: el familiar si es alumno,
    o la propia ficha en los demás roles."""
    ficha = ficha_de(db, usuario)
    if ficha is not None and usuario.rol == "ALUMNO":
        return ficha.familiar
    return ficha


def obtener_correo(db, usuario):
    registro = _donde_esta_el_contacto(db, usuario)
    return registro.email if registro else None


def obtener_telefono(db, usuario):
    registro = _donde_esta_el_contacto(db, usuario)
    return registro.telefono if registro else None


def guardar_contacto(db, usuario, telefono=None, email=None) -> None:
    """Guarda el teléfono y/o el correo (los que no sean None). No hace commit."""
    ficha = ficha_de(db, usuario)
    if ficha is None:
        raise ValueError("La cuenta no tiene una ficha asociada")

    registro = ficha
    if usuario.rol == "ALUMNO":
        # Si el alumno todavía no tiene familiar, se le crea uno vacío.
        if ficha.familiar is None:
            ficha.familiar = Familiar()
            db.add(ficha.familiar)
        registro = ficha.familiar

    if telefono is not None:
        registro.telefono = telefono or None   # texto vacío = borrar el dato
    if email is not None:
        registro.email = email or None


def familiar_a_dict(familiar):
    """Datos del familiar para enviarlos a la app (o None si no tiene)."""
    if familiar is None:
        return None
    return {
        "id_familiar": familiar.id_familiar,
        "nombres": familiar.nombres,
        "apellidos": familiar.apellidos,
        "dni": familiar.dni,
        "telefono": familiar.telefono,
        "email": familiar.email,
        "direccion": familiar.direccion,
    }
