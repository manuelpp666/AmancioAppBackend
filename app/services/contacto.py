"""Correo y teléfono de una cuenta, sea cual sea su rol.

Personal (docente, admin, auxiliar, psicólogo): en su propio perfil.
Alumno: la tabla `alumno` no los tiene; quien recibe los avisos es el apoderado,
así que se guardan en `familiar` (el de parentesco principal primero).
"""
from app.models.alumno import Alumno
from app.models.docente import Docente
from app.models.familiar import Familiar
from app.models.personal import Administrador, Auxiliar, Psicologo
from app.models.relacion_familiar import RelacionFamiliar

PERFIL_POR_ROL = {"DOCENTE": Docente, "ADMIN": Administrador,
                  "AUXILIAR": Auxiliar, "PSICOLOGO": Psicologo}
_PRIORIDAD = ("APODERADO", "MADRE", "PADRE")


def perfil_de(db, usuario):
    """Ficha del usuario según su rol (Alumno, Docente, ...), o None."""
    if usuario.rol == "ALUMNO":
        return db.query(Alumno).filter(Alumno.id_usuario == usuario.id_usuario).first()
    modelo = PERFIL_POR_ROL.get(usuario.rol)
    if not modelo:
        return None
    return db.query(modelo).filter(modelo.id_usuario == usuario.id_usuario).first()


def _relaciones(db, id_alumno: int):
    rels = db.query(RelacionFamiliar).filter(RelacionFamiliar.id_alumno == id_alumno).all()

    def orden(r):
        t = (r.tipo_parentesco or "").strip().upper()
        return _PRIORIDAD.index(t) if t in _PRIORIDAD else len(_PRIORIDAD)
    return sorted(rels, key=orden)


def serializar_familiar(familiar: Familiar, parentesco: str | None = None) -> dict:
    return {
        "id_familiar": familiar.id_familiar,
        "nombre": f"{familiar.nombres} {familiar.apellidos}",
        "nombres": familiar.nombres, "apellidos": familiar.apellidos,
        "dni": familiar.dni, "parentesco": parentesco or "",
        "telefono": familiar.telefono, "email": familiar.email,
        "direccion": familiar.direccion,
    }


def familiares_de(db, id_alumno: int) -> list[dict]:
    rels = db.query(RelacionFamiliar).filter(RelacionFamiliar.id_alumno == id_alumno).all()
    return [serializar_familiar(r.familiar, r.tipo_parentesco) for r in rels if r.familiar]


def _leer(db, usuario, campo: str) -> str | None:
    perfil = perfil_de(db, usuario)
    if not perfil:
        return None
    if usuario.rol == "ALUMNO":
        for rel in _relaciones(db, perfil.id_alumno):
            valor = (getattr(rel.familiar, campo) or "").strip() if rel.familiar else ""
            if valor:
                return valor
        return None
    return (getattr(perfil, campo) or "").strip() or None


def _guardar(db, usuario, campo: str, valor: str | None) -> None:
    """Anota el dato donde corresponda. No hace commit."""
    limpio = (valor or "").strip() or None
    perfil = perfil_de(db, usuario)
    if not perfil:
        raise ValueError("La cuenta no tiene un perfil asociado")
    if usuario.rol != "ALUMNO":
        setattr(perfil, campo, limpio)
        return
    rels = _relaciones(db, perfil.id_alumno)
    if rels and rels[0].familiar:
        setattr(rels[0].familiar, campo, limpio)
        return
    familiar = Familiar(**{campo: limpio})
    db.add(familiar)
    db.flush()
    db.add(RelacionFamiliar(id_alumno=perfil.id_alumno, id_familiar=familiar.id_familiar,
                            tipo_parentesco="APODERADO"))


def obtener_correo(db, usuario): return _leer(db, usuario, "email")
def obtener_telefono(db, usuario): return _leer(db, usuario, "telefono")
def tiene_correo(db, usuario) -> bool: return bool(obtener_correo(db, usuario))
def guardar_correo(db, usuario, valor): _guardar(db, usuario, "email", valor)
def guardar_telefono(db, usuario, valor): _guardar(db, usuario, "telefono", valor)
