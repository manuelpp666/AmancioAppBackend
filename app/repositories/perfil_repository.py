"""Consultas SQL de las fichas de cada persona (alumno, docente, personal) y
del familiar del alumno."""
from app.database import consultar_uno, ejecutar, insertar

# Tabla donde está la ficha de cada rol. El nombre de la tabla no puede ir como
# parámetro %s, por eso sale de este diccionario fijo (nunca de lo que envía el usuario).
TABLA_POR_ROL = {
    "ALUMNO": "alumno",
    "DOCENTE": "docente",
    "ADMIN": "administrador",
    "AUXILIAR": "auxiliar",
    "PSICOLOGO": "psicologo",
}


def ficha(rol: str, id_usuario: int):
    """Todas las columnas de la ficha de una cuenta, o None."""
    tabla = TABLA_POR_ROL[rol]
    return consultar_uno(f"SELECT * FROM {tabla} WHERE id_usuario = %s", (id_usuario,))


def alumno_por_usuario(id_usuario: int):
    return consultar_uno("SELECT * FROM alumno WHERE id_usuario = %s", (id_usuario,))


def docente_por_usuario(id_usuario: int):
    return consultar_uno("SELECT * FROM docente WHERE id_usuario = %s", (id_usuario,))


def psicologo_por_usuario(id_usuario: int):
    return consultar_uno("SELECT * FROM psicologo WHERE id_usuario = %s", (id_usuario,))


def alumno_por_id(id_alumno: int):
    return consultar_uno("SELECT * FROM alumno WHERE id_alumno = %s", (id_alumno,))


def actualizar_contacto(rol: str, id_usuario: int, telefono, email) -> int:
    """Teléfono y correo en la ficha del personal (docente, admin, auxiliar, psicólogo)."""
    tabla = TABLA_POR_ROL[rol]
    return ejecutar(f"UPDATE {tabla} SET telefono = %s, email = %s WHERE id_usuario = %s",
                    (telefono, email, id_usuario))


def actualizar_direccion(id_alumno: int, direccion: str) -> int:
    return ejecutar("UPDATE alumno SET direccion = %s WHERE id_alumno = %s",
                    (direccion, id_alumno))


def actualizar_enfermedad(id_alumno: int, enfermedad) -> int:
    return ejecutar("UPDATE alumno SET enfermedad = %s WHERE id_alumno = %s",
                    (enfermedad, id_alumno))


# --- Matrícula del alumno -------------------------------------------------------

def matricula_detalle(id_alumno: int, id_anio: str):
    """Matrícula del alumno en un año con su nivel, grado y sección (sin datos de pagos)."""
    return consultar_uno("""
        SELECT m.id_matricula, m.id_anio_escolar AS anio, n.nombre AS nivel, g.nombre AS grado,
               s.nombre AS seccion, m.estado, m.condicion, m.tipo_matricula, m.fecha_matricula
        FROM matricula m
        JOIN grado g ON g.id_grado = m.id_grado
        JOIN nivel n ON n.id_nivel = g.id_nivel
        LEFT JOIN seccion s ON s.id_seccion = m.id_seccion
        WHERE m.id_alumno = %s AND m.id_anio_escolar = %s
    """, (id_alumno, id_anio))


# --- Familiar del alumno ------------------------------------------------------

def familiar_por_id(id_familiar: int):
    return consultar_uno("""
        SELECT id_familiar, dni, nombres, apellidos, telefono, email, direccion
        FROM familiar
        WHERE id_familiar = %s
    """, (id_familiar,))


def crear_familiar(telefono, email) -> int:
    return insertar("INSERT INTO familiar (telefono, email) VALUES (%s, %s)", (telefono, email))


def asignar_familiar(id_alumno: int, id_familiar: int) -> int:
    return ejecutar("UPDATE alumno SET id_familiar = %s WHERE id_alumno = %s",
                    (id_familiar, id_alumno))


def actualizar_contacto_familiar(id_familiar: int, telefono, email) -> int:
    return ejecutar("UPDATE familiar SET telefono = %s, email = %s WHERE id_familiar = %s",
                    (telefono, email, id_familiar))
