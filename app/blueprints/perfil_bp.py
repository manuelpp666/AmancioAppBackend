"""Módulo Perfil: ver y editar los datos propios, y cambiar la contraseña.

GET   /perfil/mi-perfil/<username>            ver un perfil (el propio, o cualquiera si es ADMIN)
PATCH /perfil/contacto/<username>             cambiar teléfono y/o correo
PATCH /perfil/alumno/<username>/direccion     el alumno cambia su dirección
PATCH /perfil/alumno/<username>/medicos       el alumno cambia sus datos médicos
POST  /perfil/auth/change-password            cambiar la contraseña
"""
from flask import Blueprint, jsonify

from app.auth import exigir_dueno_o_roles, jwt_required, usuario_actual
from app.database import get_db
from app.errors import ApiError
from app.models.usuario import Usuario
from app.security import get_password_hash, verify_password
from app.services import contacto
from app.utils import EMAIL_RE, a_dict, extraer_dni, json_requerido, texto

bp = Blueprint("perfil", __name__, url_prefix="/perfil")


# --- Funciones de ayuda ------------------------------------------------------

def _buscar_usuario(db, username: str) -> Usuario:
    """Usuario con ese username, o error 404."""
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise ApiError(404, "Usuario no encontrado")
    return user


def _usuario_propio(db, username: str) -> Usuario:
    """Usuario de la URL, que además debe ser el mismo que inició sesión."""
    user = _buscar_usuario(db, username)
    if user.id_usuario != usuario_actual()["id"]:
        raise ApiError(403, "No puedes editar un perfil ajeno")
    return user


def _alumno_propio(db, username: str):
    """Ficha del alumno que inició sesión (para las rutas solo de alumnos)."""
    user = _usuario_propio(db, username)
    alumno = contacto.ficha_de(db, user)
    if alumno is None:
        raise ApiError(404, "Datos de alumno no encontrados")
    return alumno


# --- Rutas -------------------------------------------------------------------

@bp.get("/mi-perfil/<username>")
@jwt_required()
def mi_perfil(username):
    db = get_db()
    user = _buscar_usuario(db, username)
    # Solo el dueño del perfil o un ADMIN pueden verlo.
    exigir_dueno_o_roles(user.id_usuario, "ADMIN")

    ficha = contacto.ficha_de(db, user)
    if ficha is None:
        raise ApiError(404, f"Datos de {user.rol.lower()} no encontrados")

    # Docente, admin, auxiliar o psicólogo: se devuelven todas las columnas de su ficha.
    if user.rol != "ALUMNO":
        return jsonify({"rol": user.rol, "datos": a_dict(ficha)})

    # Alumno: solo los datos que la app necesita, más el contacto y su familiar.
    datos = {
        "id_alumno": ficha.id_alumno,
        "id_usuario": ficha.id_usuario,
        "dni": ficha.dni,
        "nombres": ficha.nombres,
        "apellidos": ficha.apellidos,
        "fecha_nacimiento": ficha.fecha_nacimiento,
        "genero": ficha.genero,
        "direccion": ficha.direccion,
        "enfermedad": ficha.enfermedad,
        "talla_polo": ficha.talla_polo,
        "colegio_procedencia": ficha.colegio_procedencia,
        "estado_ingreso": ficha.estado_ingreso,
        "telefono": contacto.obtener_telefono(db, user),   # vienen del familiar
        "email": contacto.obtener_correo(db, user),
    }
    return jsonify({"rol": user.rol, "datos": datos,
                    "familiar": contacto.familiar_a_dict(ficha.familiar)})


@bp.patch("/contacto/<username>")
@jwt_required()
def actualizar_contacto(username):
    db = get_db()
    user = _usuario_propio(db, username)
    datos = json_requerido()

    # Los dos campos son opcionales: se cambia solo lo que se envíe.
    telefono = texto(datos, "telefono", minimo=0, maximo=9, requerido=False)  # 9 dígitos
    email = texto(datos, "email", minimo=0, maximo=100, requerido=False)
    if email and not EMAIL_RE.match(email):
        raise ApiError(400, "El correo no tiene un formato válido")

    try:
        contacto.guardar_contacto(db, user, telefono=telefono, email=email)
    except ValueError as e:
        raise ApiError(404, str(e))
    db.commit()   # guardar los cambios en la base

    return jsonify({
        "message": "Datos de contacto actualizados con éxito",
        "datos": {"telefono": contacto.obtener_telefono(db, user),
                  "email": contacto.obtener_correo(db, user)},
    })


@bp.patch("/alumno/<username>/direccion")
@jwt_required("ALUMNO")
def actualizar_direccion(username):
    db = get_db()
    alumno = _alumno_propio(db, username)
    alumno.direccion = texto(json_requerido(), "direccion", minimo=3, maximo=300)
    db.commit()
    return jsonify({"message": "Dirección actualizada con éxito", "direccion": alumno.direccion})


@bp.patch("/alumno/<username>/medicos")
@jwt_required("ALUMNO")
def actualizar_medicos(username):
    db = get_db()
    alumno = _alumno_propio(db, username)
    enfermedad = texto(json_requerido(), "enfermedad", minimo=0, maximo=150, requerido=False)
    alumno.enfermedad = enfermedad or None   # vacío = sin datos médicos
    db.commit()
    return jsonify({"message": "Datos médicos actualizados", "enfermedad": alumno.enfermedad})


@bp.post("/auth/change-password")
@jwt_required()
def change_password():
    db = get_db()
    datos = json_requerido()
    actual = texto(datos, "current_password", minimo=1, maximo=200, strip=False)
    nueva = texto(datos, "new_password", minimo=8, maximo=200, strip=False)

    # Se cambia la clave del usuario que inició sesión (el del token).
    user = db.get(Usuario, usuario_actual()["id"])
    if user is None:
        raise ApiError(404, "Usuario no encontrado")

    if not verify_password(actual, user.password_hash):
        raise ApiError(400, "La contraseña actual es incorrecta")
    if nueva.strip() == extraer_dni(user.username):
        raise ApiError(400, "La nueva contraseña no puede ser tu DNI. Elige una distinta.")

    user.password_hash = get_password_hash(nueva)   # se guarda el hash, nunca la clave
    user.debe_cambiar_password = False
    db.commit()
    return jsonify({"message": "Contraseña actualizada con éxito"})
