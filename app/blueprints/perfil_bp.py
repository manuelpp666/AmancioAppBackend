"""Módulo 10 — Perfil, primer ingreso y cambio de contraseña.

GET   /perfil/mi-perfil/<username>
PATCH /perfil/contacto/<username>
PATCH /perfil/alumno/<username>/direccion
PATCH /perfil/alumno/<username>/medicos
POST  /perfil/auth/change-password
GET   /perfil/auth/primer-ingreso
POST  /perfil/auth/registrar-correo
"""
from flask import Blueprint, jsonify

from app.auth import exigir_dueno_o_roles, jwt_required, usuario_actual
from app.database import get_db
from app.errors import ApiError
from app.models.usuario import Usuario
from app.security import get_password_hash, verify_password
from app.services import contacto
from app.services.colegio import exigir_cambio_password, exigir_correo
from app.utils import EMAIL_RE, a_dict, extraer_dni, json_requerido, texto

bp = Blueprint("perfil", __name__, url_prefix="/perfil")


def _usuario_por_username(db, username: str) -> Usuario:
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        raise ApiError(404, "Usuario no encontrado")
    return user


def _usuario_propio(db, username: str) -> Usuario:
    """Usuario del path, que además tiene que ser el de la sesión."""
    user = _usuario_por_username(db, username)
    if user.id_usuario != usuario_actual()["id"]:
        raise ApiError(403, "No puedes editar un perfil ajeno")
    return user


def _validar_email(valor: str | None) -> str | None:
    if valor and not EMAIL_RE.match(valor):
        raise ApiError(400, "El correo no tiene un formato válido")
    return valor


@bp.get("/mi-perfil/<username>")
@jwt_required()
def mi_perfil(username):
    db = get_db()
    user = _usuario_por_username(db, username)
    # Mejora respecto al original: solo el dueño (o un ADMIN) puede ver un perfil.
    exigir_dueno_o_roles(user.id_usuario, "ADMIN")

    ficha = contacto.perfil_de(db, user)
    if user.rol not in ("ALUMNO", *contacto.PERFIL_POR_ROL):
        raise ApiError(400, "Rol no soportado")
    if not ficha:
        raise ApiError(404, f"Datos de {user.rol.lower()} no encontrados")

    if user.rol == "ALUMNO":
        datos = {
            "id_alumno": ficha.id_alumno, "id_usuario": ficha.id_usuario, "dni": ficha.dni,
            "nombres": ficha.nombres, "apellidos": ficha.apellidos,
            "fecha_nacimiento": ficha.fecha_nacimiento, "genero": ficha.genero,
            "direccion": ficha.direccion, "enfermedad": ficha.enfermedad,
            "talla_polo": ficha.talla_polo, "colegio_procedencia": ficha.colegio_procedencia,
            "estado_ingreso": ficha.estado_ingreso,
            "telefono": contacto.obtener_telefono(db, user),
            "email": contacto.obtener_correo(db, user),
        }
        return jsonify({"rol": user.rol, "datos": datos,
                        "familiares": contacto.familiares_de(db, ficha.id_alumno)})
    return jsonify({"rol": user.rol, "datos": a_dict(ficha)})


@bp.patch("/contacto/<username>")
@jwt_required()
def actualizar_contacto(username):
    db = get_db()
    user = _usuario_propio(db, username)
    datos = json_requerido()
    # 9 = largo de la columna `telefono` en la base.
    telefono = texto(datos, "telefono", minimo=0, maximo=9, requerido=False)
    email = _validar_email(texto(datos, "email", minimo=0, maximo=100, requerido=False))
    try:
        if telefono is not None:
            contacto.guardar_telefono(db, user, telefono)
        if email is not None:
            contacto.guardar_correo(db, user, email)
    except ValueError as e:
        db.rollback()
        raise ApiError(404, str(e))
    db.commit()
    return jsonify({"message": "Datos de contacto actualizados con éxito",
                    "datos": {"telefono": contacto.obtener_telefono(db, user),
                              "email": contacto.obtener_correo(db, user)}})


def _alumno_propio(db, username: str):
    user = _usuario_propio(db, username)
    if user.rol != "ALUMNO":
        raise ApiError(403, "Solo un estudiante puede editar estos datos")
    alumno = contacto.perfil_de(db, user)
    if not alumno:
        raise ApiError(404, "Datos de alumno no encontrados")
    return alumno


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
    valor = texto(json_requerido(), "enfermedad", minimo=0, maximo=150, requerido=False)
    alumno.enfermedad = valor or None
    db.commit()
    return jsonify({"message": "Datos médicos actualizados", "enfermedad": alumno.enfermedad})


@bp.post("/auth/change-password")
@jwt_required()
def change_password():
    db = get_db()
    datos = json_requerido()
    user = _usuario_por_username(db, texto(datos, "username", minimo=3, maximo=50))
    if user.id_usuario != usuario_actual()["id"]:
        raise ApiError(403, "No puedes cambiar la contraseña de otro usuario")

    actual = texto(datos, "current_password", minimo=1, maximo=200, strip=False)
    nueva = texto(datos, "new_password", minimo=8, maximo=200, strip=False)

    if not verify_password(actual, user.password_hash):
        raise ApiError(400, "La contraseña actual es incorrecta")
    if nueva.strip() == extraer_dni(user.username):
        raise ApiError(400, "La nueva contraseña no puede ser tu DNI. Elige una distinta.")

    user.password_hash = get_password_hash(nueva)
    user.debe_cambiar_password = False
    db.commit()
    return jsonify({"message": "Contraseña actualizada con éxito"})


@bp.get("/auth/primer-ingreso")
@jwt_required()
def estado_primer_ingreso():
    db = get_db()
    user = db.query(Usuario).filter(Usuario.id_usuario == usuario_actual()["id"]).first()
    if not user:
        raise ApiError(404, "Usuario no encontrado")
    correo = contacto.obtener_correo(db, user)
    return jsonify({
        "debe_cambiar_password": bool(user.debe_cambiar_password) and exigir_cambio_password(db),
        "debe_registrar_correo": exigir_correo(db) and not correo,
        "es_alumno": user.rol == "ALUMNO",
        "email_actual": correo,
    })


@bp.post("/auth/registrar-correo")
@jwt_required()
def registrar_correo():
    db = get_db()
    user = db.query(Usuario).filter(Usuario.id_usuario == usuario_actual()["id"]).first()
    if not user:
        raise ApiError(404, "Usuario no encontrado")
    email = _validar_email(texto(json_requerido(), "email", minimo=5, maximo=100))
    try:
        contacto.guardar_correo(db, user, email)
    except ValueError as e:
        db.rollback()
        raise ApiError(400, str(e))
    db.commit()
    return jsonify({"message": "Correo registrado con éxito", "email": email})
