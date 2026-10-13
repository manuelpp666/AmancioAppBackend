"""Reglas del perfil: ver los datos y la matrícula, editar el contacto, la
dirección y los datos médicos, y cambiar la contraseña.

¿Dónde está el correo y el teléfono?
- Docente, administrador, auxiliar y psicólogo: en su propia ficha.
- Alumno: la tabla `alumno` no los tiene; se usan los de su familiar
  (cada alumno tiene uno solo, en `alumno.id_familiar`).
"""
import json

from app.auth import exigir_dueno_o_roles
from app.database import get_db
from app.errors import ApiError
from app.repositories import perfil_repository, usuario_repository
from app.services import academico_service
from app.security import get_password_hash, verify_password
from app.utils import EMAIL_RE, extraer_dni, texto


# --- Ayudas -------------------------------------------------------------------

def _buscar_usuario(username: str) -> dict:
    user = usuario_repository.buscar_por_username(username)
    if user is None:
        raise ApiError(404, "Usuario no encontrado")
    return user


def _usuario_propio(usuario: dict, username: str) -> dict:
    """Usuario de la URL, que además debe ser el mismo que inició sesión."""
    user = _buscar_usuario(username)
    if user["id_usuario"] != usuario["id"]:
        raise ApiError(403, "No puedes editar un perfil ajeno")
    return user


def _alumno_propio(usuario: dict, username: str) -> dict:
    user = _usuario_propio(usuario, username)
    alumno = perfil_repository.alumno_por_usuario(user["id_usuario"])
    if alumno is None:
        raise ApiError(404, "Datos de alumno no encontrados")
    return alumno


# --- Ver perfil ---------------------------------------------------------------

def ver_perfil(usuario: dict, username: str) -> dict:
    user = _buscar_usuario(username)
    exigir_dueno_o_roles(usuario, user["id_usuario"], "ADMIN")   # dueño o ADMIN

    ficha = perfil_repository.ficha(user["rol"], user["id_usuario"])
    if ficha is None:
        raise ApiError(404, f"Datos de {user['rol'].lower()} no encontrados")

    # Docente, admin, auxiliar o psicólogo: todas las columnas de su ficha.
    if user["rol"] != "ALUMNO":
        if isinstance(ficha.get("permisos"), str):            # admin: texto JSON → lista
            ficha["permisos"] = json.loads(ficha["permisos"])
        return {"rol": user["rol"], "datos": ficha}

    # Alumno: los datos que la app necesita, más el contacto de su familiar.
    familiar = None
    if ficha["id_familiar"] is not None:
        familiar = perfil_repository.familiar_por_id(ficha["id_familiar"])
    datos = {
        "id_alumno": ficha["id_alumno"],
        "id_usuario": ficha["id_usuario"],
        "dni": ficha["dni"],
        "nombres": ficha["nombres"],
        "apellidos": ficha["apellidos"],
        "fecha_nacimiento": ficha["fecha_nacimiento"],
        "genero": ficha["genero"],
        "direccion": ficha["direccion"],
        "enfermedad": ficha["enfermedad"],
        "talla_polo": ficha["talla_polo"],
        "colegio_procedencia": ficha["colegio_procedencia"],
        "estado_ingreso": ficha["estado_ingreso"],
        "telefono": familiar["telefono"] if familiar else None,
        "email": familiar["email"] if familiar else None,
    }
    return {"rol": user["rol"], "datos": datos, "familiar": familiar}


def ver_matricula(usuario: dict) -> dict:
    """Estado de la matrícula del alumno en el año activo (sin información económica)."""
    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    if alumno is None:
        raise ApiError(404, "Datos de alumno no encontrados")
    anio = academico_service.anio_activo()
    matricula = perfil_repository.matricula_detalle(alumno["id_alumno"], anio["id_anio_escolar"])
    if matricula is None:
        raise ApiError(404, f"No estás matriculado en el año {anio['id_anio_escolar']}")
    return matricula


# --- Editar ---------------------------------------------------------------------

def _valor_final(enviado, registro_actual, campo: str):
    """Valor a guardar: si se envió el campo, ese ("" = borrar el dato);
    si no se envió, se conserva el valor que ya tenía."""
    if enviado is not None:
        return enviado or None
    if registro_actual is None:
        return None
    return registro_actual[campo]


def actualizar_contacto(usuario: dict, username: str, datos: dict) -> dict:
    user = _usuario_propio(usuario, username)

    # Los dos campos son opcionales: se cambia solo lo que se envíe.
    telefono = texto(datos, "telefono", minimo=0, maximo=9, requerido=False)
    email = texto(datos, "email", minimo=0, maximo=100, requerido=False)
    if email and not EMAIL_RE.match(email):
        raise ApiError(400, "El correo no tiene un formato válido")

    ficha = perfil_repository.ficha(user["rol"], user["id_usuario"])
    if ficha is None:
        raise ApiError(404, "La cuenta no tiene una ficha asociada")

    # ¿Dónde se guarda? En el familiar si es alumno; en la ficha si no.
    familiar = None
    if user["rol"] == "ALUMNO" and ficha["id_familiar"] is not None:
        familiar = perfil_repository.familiar_por_id(ficha["id_familiar"])
    actual = familiar if user["rol"] == "ALUMNO" else ficha

    nuevo_telefono = _valor_final(telefono, actual, "telefono")
    nuevo_email = _valor_final(email, actual, "email")

    db = get_db()
    try:
        if user["rol"] != "ALUMNO":
            perfil_repository.actualizar_contacto(user["rol"], user["id_usuario"],
                                                  nuevo_telefono, nuevo_email)
        elif familiar is not None:
            perfil_repository.actualizar_contacto_familiar(familiar["id_familiar"],
                                                           nuevo_telefono, nuevo_email)
        else:
            # Alumno sin familiar: DOS cambios relacionados (crear el familiar y
            # enlazarlo al alumno). Si el segundo falla, el ROLLBACK deshace el primero.
            id_familiar = perfil_repository.crear_familiar(nuevo_telefono, nuevo_email)
            perfil_repository.asignar_familiar(ficha["id_alumno"], id_familiar)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Datos de contacto actualizados con éxito",
            "datos": {"telefono": nuevo_telefono, "email": nuevo_email}}


def actualizar_direccion(usuario: dict, username: str, datos: dict) -> dict:
    alumno = _alumno_propio(usuario, username)
    direccion = texto(datos, "direccion", minimo=3, maximo=300)

    db = get_db()
    try:
        perfil_repository.actualizar_direccion(alumno["id_alumno"], direccion)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Dirección actualizada con éxito", "direccion": direccion}


def actualizar_medicos(usuario: dict, username: str, datos: dict) -> dict:
    alumno = _alumno_propio(usuario, username)
    enfermedad = texto(datos, "enfermedad", minimo=0, maximo=150, requerido=False) or None

    db = get_db()
    try:
        perfil_repository.actualizar_enfermedad(alumno["id_alumno"], enfermedad)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Datos médicos actualizados", "enfermedad": enfermedad}


def cambiar_password(usuario: dict, datos: dict) -> dict:
    actual = texto(datos, "current_password", minimo=1, maximo=200, strip=False)
    nueva = texto(datos, "new_password", minimo=8, maximo=200, strip=False)

    # Se cambia la clave del usuario que inició sesión (el del token).
    user = usuario_repository.buscar_por_id(usuario["id"])
    if user is None:
        raise ApiError(404, "Usuario no encontrado")

    # Reglas de negocio
    if not verify_password(actual, user["password_hash"]):
        raise ApiError(400, "La contraseña actual es incorrecta")
    if nueva.strip() == extraer_dni(user["username"]):
        raise ApiError(400, "La nueva contraseña no puede ser tu DNI. Elige una distinta.")
    if verify_password(nueva, user["password_hash"]):
        raise ApiError(400, "La nueva contraseña debe ser distinta de la actual")

    db = get_db()
    try:
        # Guarda el hash (nunca la clave) y apaga la marca de primer ingreso.
        usuario_repository.cambiar_password(user["id_usuario"], get_password_hash(nueva))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Contraseña actualizada con éxito"}
