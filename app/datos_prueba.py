"""Preparar la base de datos: crear las tablas y cargar los datos de prueba.

Se usa desde la consola:
    flask --app run crear-tablas       ejecuta database/schema.sql (no borra nada)
    flask --app run datos-prueba       agrega los datos de prueba que falten
    flask --app run reiniciar-demo     deja la demo como al principio (claves = DNI, bimestre 3 abierto)

Usuarios de prueba (contraseña = su DNI, como en el colegio):
    ADM-11111111  Ana     administrador
    DOC-22222222  Carlos  docente   → Matemática (1ro A y 3ro A)
    DOC-66666666  María   docente   → Comunicación y Ciencia y Tecnología
    AUX-77777777  Jorge   auxiliar  → registra asistencia y conducta
    PSI-88888888  Elena   psicóloga → atiende las citas
    ALU-33333333  Lucía   alumna    → 3ro A ┐ hermanos: comparten
    ALU-44444444  Mateo   alumno    → 1ro A ┘ la misma mamá (Rosa)
    ALU-71111111  Sofía   alumna    → 3ro A
    ALU-72222222  Diego   alumno    → 3ro A
    ALU-73333333 / 74444444 / 75555555 / 76666666 / 79999999
                  Valeria, Andrés, Camila, Joaquín y Renata → 3ro A (3ro A tiene 8 alumnos)

Datos académicos: año 2026 con 4 bimestres; secciones 1ro A, 3ro A y 3ro B de
Secundaria; horario, material, una clase virtual, asistencia de 3 fechas, 2 reportes
de conducta, 2 citas (atendida y pendiente) y NOTAS de 3ro A en Matemática y
Comunicación: bimestres 1 y 2 CERRADOS (ya están en la libreta) y bimestre 3 ABIERTO.
TAREAS en Matemática de 3ro A: una vencida (Lucía entregó a tiempo y está calificada,
Sofía entregó tarde y falta calificar, el resto no entregó) y otra con fecha futura.
MENSAJES: una conversación entre Lucía y el profesor Carlos (el último mensaje, sin leer).
NOTIFICACIONES de ejemplo y una OPERACIÓN SIN CONEXIÓN ya sincronizada (la entrega de Sofía).

DEMO COMPLETA (sección 14): además hay datos en TODOS los apartados, con fechas relativas
a hoy: tareas, materiales y clases virtuales en los 3 cursos (también en 1ro A), notas
del 4.º bimestre, asistencia de los últimos 8 días hábiles, reportes (uno de hoy y uno
anulado), citas (una HOY), varias conversaciones y avisos sin leer para cada rol.

PRIMER INGRESO: Mateo tiene `debe_cambiar_password = 1` (aún usa su DNI y la app
le obliga a cambiarla). Las demás cuentas están marcadas como si ya la hubieran
cambiado, para poder probar sin ese paso.
"""
from datetime import date, timedelta

from app.database import consultar_todos, consultar_uno, ejecutar, get_db, insertar
from app.repositories import cursos_repository, nota_repository
from app.security import get_password_hash
from app.services import nota_service

ANIO = "2026"
USUARIO_PRIMER_INGRESO = "ALU-44444444"


# =============================================================================
# Datos de prueba
# =============================================================================

def cargar_datos_prueba() -> list[str]:
    """Agrega lo que falte. Todo va en UNA transacción: si algo falla, no queda nada a medias."""
    db = get_db()
    try:
        creados = []
        creados += _usuarios()
        creados += _academico()
        creados += _matriculas()
        creados += _conducta()
        creados += _citas()
        creados += _horario()
        creados += _clases_virtuales()
        creados += _asistencia()
        creados += _notas()
        creados += _tareas()
        creados += _mensajes()
        creados += _notificaciones()
        creados += _operacion_offline()
        creados += _demo_completa()
        db.commit()
        return creados
    except Exception:
        db.rollback()
        raise


def reiniciar_demo() -> None:
    """Deja la demostración como al principio:
    - contraseña = DNI en todos los usuarios de prueba (solo Mateo en primer ingreso);
    - bimestres 3 y 4 ABIERTOS otra vez (se quitan de la libreta), para poder
      volver a probar "cerrar bimestre"."""
    db = get_db()
    try:
        for username, *_ in _CUENTAS:
            dni = username.split("-")[1]
            ejecutar("""
                UPDATE usuario SET password_hash = %s, debe_cambiar_password = %s
                WHERE username = %s
            """, (get_password_hash(dni), username == USUARIO_PRIMER_INGRESO, username))

        ejecutar("DELETE FROM cierre_bimestre WHERE bimestre >= 3")
        ejecutar("UPDATE resumen_nota SET nota_bimestre3 = NULL, nota_bimestre4 = NULL")
        for fila in consultar_todos("SELECT id_matricula, id_curso FROM resumen_nota"):
            nota_service.actualizar_promedio_final(fila["id_matricula"], fila["id_curso"])
        db.commit()
    except Exception:
        db.rollback()
        raise


# --- Ayudas -------------------------------------------------------------------

def _id(sql: str, params: tuple = ()):
    """Primer valor de la primera fila de un SELECT (normalmente un id), o None."""
    fila = consultar_uno(sql, params)
    return next(iter(fila.values())) if fila else None


def _tabla_vacia(tabla: str) -> bool:
    return _id(f"SELECT COUNT(*) FROM {tabla}") == 0


def _id_usuario(username: str):
    return _id("SELECT id_usuario FROM usuario WHERE username = %s", (username,))


def _id_alumno(username: str):
    return _id("""SELECT a.id_alumno FROM alumno a JOIN usuario u ON u.id_usuario = a.id_usuario
                  WHERE u.username = %s""", (username,))


def _id_docente(username: str):
    return _id("""SELECT d.id_docente FROM docente d JOIN usuario u ON u.id_usuario = d.id_usuario
                  WHERE u.username = %s""", (username,))


def _id_seccion(grado: str, nombre: str):
    return _id("""SELECT s.id_seccion FROM seccion s
                  JOIN grado g ON g.id_grado = s.id_grado
                  JOIN nivel n ON n.id_nivel = g.id_nivel
                  WHERE n.nombre = 'Secundaria' AND g.nombre = %s AND s.nombre = %s
                    AND s.id_anio_escolar = %s""", (grado, nombre, ANIO))


def _id_carga(curso: str, grado: str, seccion: str):
    return _id("""SELECT ca.id_carga_academica FROM carga_academica ca
                  JOIN curso c ON c.id_curso = ca.id_curso
                  WHERE c.nombre = %s AND ca.id_seccion = %s""",
               (curso, _id_seccion(grado, seccion)))


# --- 1. Usuarios ----------------------------------------------------------------

# (username, rol, nombres, apellidos, tabla de la ficha, datos extra)
_CUENTAS = [
    ("ADM-11111111", "ADMIN", "Ana", "Torres Ruiz", "administrador",
     {"email": "admin@example.com", "telefono": "911111111", "permisos": '["*"]'}),
    ("DOC-22222222", "DOCENTE", "Carlos", "Mendoza Paz", "docente",
     {"email": "carlos@example.com", "telefono": "922222222", "especialidad": "Matemática",
      "visible_web": 1}),
    ("DOC-66666666", "DOCENTE", "María", "Salazar Vega", "docente",
     {"email": "maria@example.com", "telefono": "966666666", "especialidad": "Comunicación",
      "visible_web": 1}),
    ("AUX-77777777", "AUXILIAR", "Jorge", "Ramos Díaz", "auxiliar",
     {"email": "jorge@example.com", "telefono": "977777777"}),
    ("PSI-88888888", "PSICOLOGO", "Elena", "Castro Rivas", "psicologo",
     {"email": "elena@example.com", "telefono": "988888888"}),
    ("ALU-33333333", "ALUMNO", "Lucía", "Quispe Flores", "alumno", {"genero": "F"}),
    ("ALU-44444444", "ALUMNO", "Mateo", "Quispe Flores", "alumno", {"genero": "M"}),
    ("ALU-71111111", "ALUMNO", "Sofía", "Ramírez Torres", "alumno", {"genero": "F"}),
    ("ALU-72222222", "ALUMNO", "Diego", "Castillo León", "alumno", {"genero": "M"}),
    ("ALU-73333333", "ALUMNO", "Valeria", "Huamán Rojas", "alumno", {"genero": "F"}),
    ("ALU-74444444", "ALUMNO", "Andrés", "Paredes Silva", "alumno", {"genero": "M"}),
    ("ALU-75555555", "ALUMNO", "Camila", "Soto Medina", "alumno", {"genero": "F"}),
    ("ALU-76666666", "ALUMNO", "Joaquín", "Vargas Ríos", "alumno", {"genero": "M"}),
    ("ALU-79999999", "ALUMNO", "Renata", "Flores Cárdenas", "alumno", {"genero": "F"}),
]

# Los 8 alumnos de 3ro A (la sección de la demostración).
ALUMNOS_3RO_A = ["ALU-33333333", "ALU-71111111", "ALU-72222222", "ALU-73333333",
                 "ALU-74444444", "ALU-75555555", "ALU-76666666", "ALU-79999999"]


def _familiar_rosa() -> int:
    """La mamá de Lucía y Mateo (se crea si no existe)."""
    id_familiar = _id("SELECT id_familiar FROM familiar WHERE dni = '55555555'")
    if id_familiar is None:
        id_familiar = insertar("""
            INSERT INTO familiar (dni, nombres, apellidos, telefono, email, direccion)
            VALUES ('55555555', 'Rosa', 'Quispe Flores', '955555555', 'rosa.quispe@example.com',
                    'Av. Los Próceres 123, Lima')
        """)
    return id_familiar


def _usuarios() -> list[str]:
    creados = []
    for username, rol, nombres, apellidos, tabla, extra in _CUENTAS:
        if _id_usuario(username) is not None:
            continue
        dni = username.split("-")[1]
        id_usuario = insertar("""
            INSERT INTO usuario (username, password_hash, rol, activo, debe_cambiar_password)
            VALUES (%s, %s, %s, 1, %s)
        """, (username, get_password_hash(dni), rol, username == USUARIO_PRIMER_INGRESO))

        # La ficha: columnas comunes + las propias de cada rol.
        columnas = {"id_usuario": id_usuario, "dni": dni, "nombres": nombres,
                    "apellidos": apellidos, **extra}
        if rol == "ALUMNO":
            columnas.update({"direccion": "Av. Los Próceres 123, Lima",
                             "estado_ingreso": "ESTUDIANTE", "relacion_fraternal": 0})
            if apellidos == "Quispe Flores":          # Lucía y Mateo: hijos de Rosa
                columnas["id_familiar"] = _familiar_rosa()
                columnas["relacion_fraternal"] = 1
        nombres_col = ", ".join(columnas)
        marcas = ", ".join(["%s"] * len(columnas))
        insertar(f"INSERT INTO {tabla} ({nombres_col}) VALUES ({marcas})", tuple(columnas.values()))
        creados.append(username)
    return creados


# --- 2. Estructura académica ------------------------------------------------------

def _academico() -> list[str]:
    if _id("SELECT id_anio_escolar FROM anio_escolar WHERE id_anio_escolar = %s", (ANIO,)):
        return []

    insertar("""INSERT INTO anio_escolar (id_anio_escolar, fecha_inicio, fecha_fin, activo, tipo)
                VALUES (%s, '2026-03-09', '2026-12-18', 1, 'REGULAR')""", (ANIO,))
    bimestres = [("2026-03-09", "2026-05-08"), ("2026-05-18", "2026-07-24"),
                 ("2026-08-10", "2026-10-09"), ("2026-10-19", "2026-12-18")]
    for numero, (inicio, fin) in enumerate(bimestres, start=1):
        insertar("""INSERT INTO bimestre (id_anio_escolar, numero, fecha_inicio, fecha_fin)
                    VALUES (%s, %s, %s, %s)""", (ANIO, numero, inicio, fin))

    # Niveles y grados (orden 1 a 11: primero Primaria y luego Secundaria).
    primaria = insertar("INSERT INTO nivel (nombre) VALUES ('Primaria')")
    secundaria = insertar("INSERT INTO nivel (nombre) VALUES ('Secundaria')")
    nombres = ["1ro", "2do", "3ro", "4to", "5to", "6to"]
    grados_sec = {}
    for orden, nombre in enumerate(nombres, start=1):
        insertar("INSERT INTO grado (id_nivel, nombre, orden) VALUES (%s, %s, %s)",
                 (primaria, nombre, orden))
    for orden, nombre in enumerate(nombres[:5], start=7):
        grados_sec[nombre] = insertar("INSERT INTO grado (id_nivel, nombre, orden) VALUES (%s, %s, %s)",
                                      (secundaria, nombre, orden))

    # Secciones del 2026: 1ro A, 3ro A y 3ro B de Secundaria.
    secciones = {}
    for grado, seccion in (("1ro", "A"), ("3ro", "A"), ("3ro", "B")):
        secciones[(grado, seccion)] = insertar("""
            INSERT INTO seccion (id_grado, id_anio_escolar, nombre, vacantes)
            VALUES (%s, %s, %s, 30)""", (grados_sec[grado], ANIO, seccion))

    # Áreas y cursos (aquí cada área tiene un curso con el mismo nombre).
    cursos = {}
    for nombre in ("Matemática", "Comunicación", "Ciencia y Tecnología"):
        id_area = insertar("INSERT INTO area (nombre) VALUES (%s)", (nombre,))
        cursos[nombre] = insertar("""
            INSERT INTO curso (id_area, nombre, minutos_semanales, es_verano)
            VALUES (%s, %s, 270, 0)""", (id_area, nombre))

    # Carga académica: qué docente dicta cada curso en 1ro A y 3ro A.
    quien_dicta = {"Matemática": "DOC-22222222", "Comunicación": "DOC-66666666",
                   "Ciencia y Tecnología": "DOC-66666666"}
    for clave in (("1ro", "A"), ("3ro", "A")):
        for curso, docente in quien_dicta.items():
            insertar("""INSERT INTO carga_academica (id_anio_escolar, id_seccion, id_curso, id_docente)
                        VALUES (%s, %s, %s, %s)""",
                     (ANIO, secciones[clave], cursos[curso], _id_docente(docente)))

    # Material de ejemplo en Matemática de 3ro A.
    mate_3a = _id_carga("Matemática", "3ro", "A")
    insertar("""INSERT INTO material_clase (id_carga_academica, titulo, descripcion, archivo_url, bimestre)
                VALUES (%s, 'Ecuaciones de primer grado', 'Teoría y 10 ejercicios resueltos.',
                        'https://example.com/ecuaciones.pdf', 1)""", (mate_3a,))
    insertar("""INSERT INTO material_clase (id_carga_academica, titulo, descripcion, archivo_url, bimestre)
                VALUES (%s, 'Sistemas de ecuaciones', 'Video explicativo del método de sustitución.',
                        'https://example.com/sistemas', 2)""", (mate_3a,))
    return [f"estructura académica {ANIO}"]


# --- 3. Matrículas -----------------------------------------------------------------

def _matriculas() -> list[str]:
    creadas = []
    en_seccion = {"ALU-33333333": ("3ro", "A"), "ALU-44444444": ("1ro", "A")}   # Lucía y Mateo
    en_seccion.update({username: ("3ro", "A") for username in ALUMNOS_3RO_A[1:]})
    for username, (grado, seccion) in en_seccion.items():
        id_alumno = _id_alumno(username)
        if _id("SELECT id_matricula FROM matricula WHERE id_alumno = %s AND id_anio_escolar = %s",
               (id_alumno, ANIO)):
            continue
        id_seccion = _id_seccion(grado, seccion)
        insertar("""
            INSERT INTO matricula (id_anio_escolar, id_alumno, id_grado, id_seccion,
                                   fecha_matricula, estado, tipo_matricula, condicion)
            SELECT %s, %s, id_grado, id_seccion, NOW(), 'MATRICULADO', 'REGULAR', 'NORMAL'
            FROM seccion WHERE id_seccion = %s
        """, (ANIO, id_alumno, id_seccion))
        creadas.append(f"matrícula de {username}")
    return creadas


# --- 4. Conducta ------------------------------------------------------------------

def _conducta() -> list[str]:
    creados = []
    if _tabla_vacia("tipo_falta"):
        tipos = {nombre: insertar("INSERT INTO tipo_falta (nombre) VALUES (%s)", (nombre,))
                 for nombre in ("Leve", "Grave", "Muy grave")}
        faltas = [
            ("Leve", "Tardanza injustificada", 1),
            ("Leve", "No portar el uniforme completo", 2),
            ("Grave", "Uso del celular en clase", 3),
            ("Grave", "Falta de respeto a un compañero", 5),
            ("Muy grave", "Agresión física", 10),
        ]
        for tipo, nombre, puntos in faltas:
            insertar("INSERT INTO nivel_conducta (id_tipo_falta, nombre, puntos) VALUES (%s, %s, %s)",
                     (tipos[tipo], nombre, puntos))
        creados.append("catálogo de faltas")

    if _tabla_vacia("reporte_conducta"):
        auxiliar = _id_usuario("AUX-77777777")
        lucia = _id_alumno("ALU-33333333")
        celular = _id("SELECT id_nivel_conducta FROM nivel_conducta WHERE nombre = 'Uso del celular en clase'")
        uniforme = _id("SELECT id_nivel_conducta FROM nivel_conducta WHERE nombre = 'No portar el uniforme completo'")
        insertar("""
            INSERT INTO reporte_conducta (id_alumno, id_nivel_conducta, registrado_por, fecha_reporte,
                                          descripcion_suceso, evidencia_url, estado)
            VALUES (%s, %s, %s, '2026-09-15 10:20:00',
                    'Usaba el celular durante el examen de Matemática.',
                    'https://example.com/evidencia-celular.jpg', 'REGISTRADO')
        """, (lucia, celular, auxiliar))
        insertar("""
            INSERT INTO reporte_conducta (id_alumno, id_nivel_conducta, registrado_por, fecha_reporte,
                                          descripcion_suceso, estado)
            VALUES (%s, %s, %s, '2026-10-02 07:50:00', 'Llegó sin la corbata del uniforme.', 'REGISTRADO')
        """, (lucia, uniforme, auxiliar))
        creados.append("2 reportes de conducta")
    return creados


# --- 5. Citas de psicología -----------------------------------------------------------

def _citas() -> list[str]:
    if not _tabla_vacia("cita_psicologia"):
        return []
    psicologo = _id("""SELECT p.id_psicologo FROM psicologo p JOIN usuario u ON u.id_usuario = p.id_usuario
                       WHERE u.username = 'PSI-88888888'""")
    insertar("""
        INSERT INTO cita_psicologia (id_alumno, id_psicologo, motivo, disponibilidad, fecha_cita,
                                     estado, observacion, fecha_solicitud)
        VALUES (%s, %s, 'Me cuesta concentrarme en clase', 'Mañanas', '2026-10-01 10:00:00',
                'ATENDIDA', 'Se recomienda organizar horarios de estudio. Seguimiento en un mes.',
                '2026-09-25 08:00:00')
    """, (_id_alumno("ALU-33333333"), psicologo))
    insertar("""
        INSERT INTO cita_psicologia (id_alumno, motivo, disponibilidad, estado)
        VALUES (%s, 'Quiero conversar sobre problemas con mis compañeros', 'Martes o jueves', 'PENDIENTE')
    """, (_id_alumno("ALU-44444444"),))
    return ["2 citas de psicología"]


# --- 6. Horario ------------------------------------------------------------------------

def _horario() -> list[str]:
    creados = []
    if _tabla_vacia("receso_horario"):
        insertar("INSERT INTO receso_horario (nombre, hora_inicio, hora_fin) VALUES ('Recreo', '10:00', '10:20')")
        creados.append("receso")

    if _tabla_vacia("horario_escolar"):
        # 4 bloques al día; el recreo va entre el 2.º y el 3.º.
        bloques = [("08:00", "09:00"), ("09:00", "10:00"), ("10:20", "11:20"), ("11:20", "12:20")]
        # Qué curso va en cada bloque. Está repartido para que ningún docente
        # tenga dos clases a la misma hora (Carlos: Matemática; María: las otras dos).
        reparto = {
            ("3ro", "A"): ["Comunicación", "Ciencia y Tecnología", "Matemática", None],
            ("1ro", "A"): ["Matemática", None, "Comunicación", "Ciencia y Tecnología"],
        }
        for (grado, seccion), cursos in reparto.items():
            for dia in range(1, 6):                        # lunes a viernes
                for (inicio, fin), curso in zip(bloques, cursos):
                    if curso is None:                      # bloque libre
                        continue
                    insertar("""INSERT INTO horario_escolar (id_carga_academica, dia_semana, hora_inicio, hora_fin)
                                VALUES (%s, %s, %s, %s)""",
                             (_id_carga(curso, grado, seccion), dia, inicio, fin))
        creados.append("horario de 1ro A y 3ro A")
    return creados


# --- 7. Clases virtuales -----------------------------------------------------------

def _clases_virtuales() -> list[str]:
    if not _tabla_vacia("clase_virtual"):
        return []
    insertar("""
        INSERT INTO clase_virtual (id_carga_academica, tema, fecha, enlace)
        VALUES (%s, 'Repaso para el examen bimestral', '2026-10-20 16:00:00',
                'https://meet.google.com/abc-defg-hij')
    """, (_id_carga("Matemática", "3ro", "A"),))
    return ["1 clase virtual"]


# --- 8. Asistencia -------------------------------------------------------------------

def _asistencia() -> list[str]:
    if not _tabla_vacia("asistencia"):
        return []
    # 3 fechas en 3ro A, con faltas y tardanzas. Cada texto tiene el estado de los 8
    # alumnos en el orden de ALUMNOS_3RO_A (Lucía, Sofía, Diego, Valeria, Andrés...).
    estados = {
        "2026-10-05": "PPTPPPFP",
        "2026-10-06": "FPPPTPPP",
        "2026-10-07": "PJPPPPFP",
    }
    for dia, letras in estados.items():
        for username, estado in zip(ALUMNOS_3RO_A, letras):
            id_matricula = _id("SELECT id_matricula FROM matricula WHERE id_alumno = %s AND id_anio_escolar = %s",
                               (_id_alumno(username), ANIO))
            insertar("INSERT INTO asistencia (id_matricula, fecha, estado, estado_original) "
                     "VALUES (%s, %s, %s, %s)",
                     (id_matricula, date.fromisoformat(dia), estado, "F" if estado == "J" else None))
    return ["asistencia de 3 fechas"]


# --- 9. Notas -----------------------------------------------------------------------

def _notas() -> list[str]:
    """Notas de 3ro A en Matemática (Carlos) y Comunicación (María): dos evaluaciones
    por bimestre en los bimestres 1, 2 y 3. Se cierran el 1 y el 2; el 3 queda abierto."""
    if not _tabla_vacia("nota"):
        return []
    # Nivel de cada alumno (su nota base): Lucía 16, Sofía 13, Diego 10, Valeria 18...
    base = dict(zip(ALUMNOS_3RO_A, (16, 13, 10, 18, 12, 15, 9, 14)))
    cursos = {"Matemática": ("DOC-22222222", 0), "Comunicación": ("DOC-66666666", -1)}
    evaluaciones = {"Práctica 1": 0, "Examen": 1}

    for curso, (docente, ajuste_curso) in cursos.items():
        carga = cursos_repository.buscar_carga(_id_carga(curso, "3ro", "A"))
        for bimestre in (1, 2, 3):
            for evaluacion, ajuste_eval in evaluaciones.items():
                for username, nivel in base.items():
                    valor = nivel + ajuste_curso + ajuste_eval + (bimestre - 2)
                    id_matricula = _id("""SELECT id_matricula FROM matricula
                                          WHERE id_alumno = %s AND id_anio_escolar = %s""",
                                       (_id_alumno(username), ANIO))
                    nota_repository.guardar_nota(id_matricula, carga["id_curso"], bimestre,
                                                 evaluacion, valor)
        # Cerrar los bimestres 1 y 2 con la misma lógica que usa el endpoint.
        for bimestre in (1, 2):
            nota_service.aplicar_cierre(carga, bimestre, _id_usuario(docente))
    return ["notas de 3ro A (bimestres 1 y 2 cerrados, 3 abierto)"]


# --- 10. Tareas y entregas -------------------------------------------------------------

def _tareas() -> list[str]:
    if not _tabla_vacia("tarea"):
        return []
    mate_3a = _id_carga("Matemática", "3ro", "A")
    vencida = insertar("""
        INSERT INTO tarea (id_carga_academica, titulo, descripcion, fecha_publicacion, fecha_entrega,
                           bimestre, archivo_adjunto_url, estado, tipo_evaluacion, peso)
        VALUES (%s, 'Ejercicios de ecuaciones', 'Resolver los 10 ejercicios de la página 45.',
                '2026-09-28 08:00:00', '2026-10-05 23:59:00', 3,
                'https://example.com/ejercicios-ecuaciones.pdf', 'ACTIVO', 'TAREA', 0)
    """, (mate_3a,))
    insertar("""
        INSERT INTO tarea (id_carga_academica, titulo, descripcion, fecha_entrega, bimestre,
                           estado, tipo_evaluacion, peso)
        VALUES (%s, 'Proyecto: sistemas de ecuaciones', 'Video de 3 minutos explicando un problema real.',
                '2026-11-20 23:59:00', 4, 'ACTIVO', 'TAREA', 0)
    """, (mate_3a,))
    # Lucía: a tiempo y calificada.
    insertar("""
        INSERT INTO entrega_tarea (id_tarea, id_alumno, archivo_url, comentario_alumno, fecha_envio,
                                   calificacion, retroalimentacion_docente)
        VALUES (%s, %s, 'https://drive.google.com/lucia-ecuaciones', 'Adjunto mis ejercicios.',
                '2026-10-04 19:30:00', 17, 'Buen trabajo, revisa el ejercicio 8.')
    """, (vencida, _id_alumno("ALU-33333333")))
    # Sofía: fuera de plazo, sin calificar.
    insertar("""
        INSERT INTO entrega_tarea (id_tarea, id_alumno, archivo_url, fecha_envio)
        VALUES (%s, %s, 'https://drive.google.com/sofia-ecuaciones', '2026-10-06 10:15:00')
    """, (vencida, _id_alumno("ALU-71111111")))
    return ["2 tareas (una con entrega calificada)"]


# --- 11. Mensajes ------------------------------------------------------------------

def _mensajes() -> list[str]:
    """Una conversación entre Lucía y el profesor Carlos. El último mensaje
    (de Lucía) está sin leer: Carlos lo ve como pendiente."""
    if not _tabla_vacia("conversacion"):
        return []
    lucia, carlos = _id_usuario("ALU-33333333"), _id_usuario("DOC-22222222")
    mensajes = [   # (remitente, contenido, fecha, leído)
        (lucia, "Profesor, ¿el ejercicio 8 de la tarea se resuelve por sustitución?", "2026-10-04 18:05:00", 1),
        (carlos, "Sí, Lucía. Despeja x en la primera ecuación y reemplázala en la segunda.", "2026-10-04 18:40:00", 1),
        (lucia, "Gracias, profesor. Ya me salió.", "2026-10-04 19:10:00", 0),
    ]
    id_conversacion = insertar("""
        INSERT INTO conversacion (usuario1_id, usuario2_id, ultimo_mensaje, fecha_actualizacion)
        VALUES (%s, %s, %s, %s)
    """, (min(lucia, carlos), max(lucia, carlos), mensajes[-1][1], mensajes[-1][2]))
    for remitente, contenido, fecha, leido in mensajes:
        insertar("""INSERT INTO mensaje (id_conversacion, remitente_id, contenido, leido, fecha_envio)
                    VALUES (%s, %s, %s, %s, %s)""", (id_conversacion, remitente, contenido, leido, fecha))
    return ["1 conversación con 3 mensajes"]


# --- 12. Notificaciones ---------------------------------------------------------------

def _notificaciones() -> list[str]:
    """Algunas notificaciones de ejemplo (en la app real las crean los services)."""
    if not _tabla_vacia("notificacion"):
        return []
    tarea_vencida = _id("SELECT id_tarea FROM tarea WHERE titulo = 'Ejercicios de ecuaciones'")
    proyecto = _id("SELECT id_tarea FROM tarea WHERE titulo = 'Proyecto: sistemas de ecuaciones'")
    conversacion = _id("SELECT MIN(id_conversacion) FROM conversacion")
    reporte = _id("SELECT MAX(id_reporte) FROM reporte_conducta")
    avisos = [   # (usuario, tipo, título, mensaje, referencia, leída, fecha)
        ("ALU-33333333", "CONDUCTA", "Nuevo reporte de conducta",
         "No portar el uniforme completo (−2 puntos)", reporte, 1, "2026-10-02 08:00:00"),
        ("ALU-33333333", "CALIFICACION", "Tu tarea fue calificada",
         "Ejercicios de ecuaciones: 17", tarea_vencida, 1, "2026-10-06 09:00:00"),
        ("DOC-22222222", "MENSAJE", "Mensaje de Lucía Quispe Flores",
         "Gracias, profesor. Ya me salió.", conversacion, 0, "2026-10-04 19:10:00"),
    ]
    # La tarea del proyecto se avisó a toda la sección.
    avisos += [(username, "TAREA", "Nueva tarea de Matemática",
                "Proyecto: sistemas de ecuaciones · entrega hasta el 20/11 23:59", proyecto, 0,
                "2026-10-13 08:00:00") for username in ALUMNOS_3RO_A]
    for username, tipo, titulo, mensaje, referencia, leida, fecha in avisos:
        insertar("""
            INSERT INTO notificacion (id_usuario, tipo, titulo, mensaje, id_referencia, leida, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (_id_usuario(username), tipo, titulo, mensaje, referencia, leida, fecha))
    return [f"{len(avisos)} notificaciones"]


# --- 13. Operación hecha sin conexión ------------------------------------------------

def _operacion_offline() -> list[str]:
    """Sofía entregó la tarea sin internet; la app la envió al volver la conexión
    con el id "demo-offline-sofia-0001". Si el celular la reenvía, la API responde
    lo mismo sin duplicar la entrega (ver app/offline.py)."""
    if not _tabla_vacia("operacion_offline"):
        return []
    tarea = _id("SELECT id_tarea FROM tarea WHERE titulo = 'Ejercicios de ecuaciones'")
    insertar("""
        INSERT INTO operacion_offline (id_operacion, id_usuario, metodo, ruta, codigo, respuesta, fecha)
        VALUES ('demo-offline-sofia-0001', %s, 'POST', %s, 201, %s, '2026-10-06 10:15:05')
    """, (_id_usuario("ALU-71111111"), f"/tareas/item/{tarea}/entregar",
          '{"fuera_de_plazo":true,"message":"Tarea entregada"}'))
    return ["1 operación sin conexión"]


# =============================================================================
# 14. Demo completa: datos en TODOS los apartados de la app
# =============================================================================
#
# Lo de arriba deja la demo mínima. Esto la completa para que cada pantalla de cada
# usuario tenga algo que mostrar: tareas y materiales en los tres cursos, notas del
# 4.º bimestre, asistencia de los últimos días, reportes, citas (una HOY), varias
# conversaciones y avisos para todos los roles.
#
# Usa fechas RELATIVAS a hoy (ayer, mañana, en 5 días...) para que la demo siempre se
# vea "al día". Se agrega una sola vez: la marca es la tarea "Ensayo: mi lugar favorito".
# En una base que ya tiene la demo mínima basta con: flask --app run datos-prueba

MARCA_DEMO_COMPLETA = "Ensayo: mi lugar favorito"


def _cuando(dias: int, hora: str) -> str:
    """Fecha y hora relativa a hoy: _cuando(-1, "18:20") = ayer a las 18:20."""
    return f"{(date.today() + timedelta(days=dias)).isoformat()} {hora}:00"


def _dias_habiles_anteriores(cantidad: int) -> list:
    """Los últimos `cantidad` días de lunes a viernes, sin contar hoy (del más antiguo al más nuevo)."""
    dias, dia = [], date.today()
    while len(dias) < cantidad:
        dia -= timedelta(days=1)
        if dia.weekday() < 5:
            dias.append(dia)
    return sorted(dias)


def _id_matricula(username: str):
    return _id("SELECT id_matricula FROM matricula WHERE id_alumno = %s AND id_anio_escolar = %s",
               (_id_alumno(username), ANIO))


def _id_falta(nombre: str):
    return _id("SELECT id_nivel_conducta FROM nivel_conducta WHERE nombre = %s", (nombre,))


def _id_tarea(titulo: str):
    return _id("SELECT id_tarea FROM tarea WHERE titulo = %s", (titulo,))


def _demo_completa() -> list[str]:
    if _id_tarea(MARCA_DEMO_COMPLETA):
        return []
    _demo_perfiles()
    _demo_notas()
    _demo_aula_virtual()
    _demo_asistencia()
    _demo_conducta()
    _demo_citas()
    _demo_mensajes()
    _demo_notificaciones()
    return ["demo completa (datos en todos los apartados)"]


def _demo_perfiles() -> None:
    """Datos personales y un apoderado para cada alumno (se ven en "Mi perfil")."""
    nacimientos = {"ALU-33333333": "2011-05-14", "ALU-44444444": "2013-08-02",
                   "ALU-71111111": "2011-02-27", "ALU-72222222": "2011-11-09",
                   "ALU-73333333": "2011-07-19", "ALU-74444444": "2011-03-30",
                   "ALU-75555555": "2011-09-05", "ALU-76666666": "2011-12-12",
                   "ALU-79999999": "2011-06-21"}
    for username, nacimiento in nacimientos.items():
        ejecutar("""
            UPDATE alumno SET fecha_nacimiento = COALESCE(fecha_nacimiento, %s),
                              talla_polo = COALESCE(talla_polo, 'M'),
                              colegio_procedencia = COALESCE(colegio_procedencia, 'I.E. Santa Rosa')
            WHERE id_alumno = %s
        """, (nacimiento, _id_alumno(username)))
    ejecutar("UPDATE alumno SET enfermedad = 'Asma leve (usa inhalador)' "
             "WHERE id_alumno = %s AND enfermedad IS NULL", (_id_alumno("ALU-33333333"),))

    # Un apoderado para los alumnos que aún no tienen (Lucía y Mateo ya tienen a Rosa).
    familiares = {
        "ALU-71111111": ("41234567", "Patricia", "Torres Vega", "941234567"),
        "ALU-72222222": ("42345678", "Luis", "Castillo Pérez", "942345678"),
        "ALU-73333333": ("43456789", "Gloria", "Rojas Díaz", "943456789"),
        "ALU-74444444": ("44567890", "Martín", "Paredes Luna", "944567890"),
        "ALU-75555555": ("45678901", "Silvia", "Medina Cruz", "945678901"),
        "ALU-76666666": ("46789012", "Raúl", "Vargas Soto", "946789012"),
        "ALU-79999999": ("47890123", "Carmen", "Cárdenas Ruiz", "947890123"),
    }
    for username, (dni, nombres, apellidos, telefono) in familiares.items():
        id_familiar = _id("SELECT id_familiar FROM familiar WHERE dni = %s", (dni,))
        if id_familiar is None:
            correo = f"{nombres.lower()}.{apellidos.split()[0].lower()}@example.com"
            id_familiar = insertar("""
                INSERT INTO familiar (dni, nombres, apellidos, telefono, email, direccion)
                VALUES (%s, %s, %s, %s, %s, 'Calle Real 456, Tumán')
            """, (dni, nombres, apellidos, telefono, correo))
        ejecutar("UPDATE alumno SET id_familiar = %s WHERE id_alumno = %s AND id_familiar IS NULL",
                 (id_familiar, _id_alumno(username)))


def _guardar_notas(carga: dict, alumnos: dict, bimestres, evaluaciones: dict, ajuste_curso: int) -> None:
    """Notas de varios alumnos (nota = nivel del alumno + ajustes, siempre entre 0 y 20)."""
    for bimestre in bimestres:
        for evaluacion, ajuste_eval in evaluaciones.items():
            for username, nivel in alumnos.items():
                valor = max(0, min(20, nivel + ajuste_curso + ajuste_eval + (bimestre - 2)))
                nota_repository.guardar_nota(_id_matricula(username), carga["id_curso"], bimestre,
                                             evaluacion, valor)


def _cerrar(carga: dict, bimestres, docente: str) -> None:
    """Cierra los bimestres indicados (si aún no lo estaban), igual que el endpoint."""
    for bimestre in bimestres:
        if bimestre not in nota_repository.bimestres_cerrados(carga["id_carga_academica"]):
            nota_service.aplicar_cierre(carga, bimestre, _id_usuario(docente))


def _demo_notas() -> None:
    """Ciencia y Tecnología de 3ro A, los tres cursos de 1ro A (Mateo) y la
    "Práctica 1" del 4.º bimestre (el que está en curso) en todos los cursos."""
    base_3a = dict(zip(ALUMNOS_3RO_A, (16, 13, 10, 18, 12, 15, 9, 14)))
    dos_evaluaciones = {"Práctica 1": 0, "Examen": 1}

    cyt_3a = cursos_repository.buscar_carga(_id_carga("Ciencia y Tecnología", "3ro", "A"))
    _guardar_notas(cyt_3a, base_3a, (1, 2, 3), dos_evaluaciones, ajuste_curso=1)
    _cerrar(cyt_3a, (1, 2), "DOC-66666666")

    docentes = {"Matemática": "DOC-22222222", "Comunicación": "DOC-66666666",
                "Ciencia y Tecnología": "DOC-66666666"}
    for curso, docente in docentes.items():
        carga_1a = cursos_repository.buscar_carga(_id_carga(curso, "1ro", "A"))
        _guardar_notas(carga_1a, {"ALU-44444444": 14}, (1, 2, 3), dos_evaluaciones, ajuste_curso=0)
        _cerrar(carga_1a, (1, 2), docente)
        _guardar_notas(carga_1a, {"ALU-44444444": 14}, (4,), {"Práctica 1": 0}, ajuste_curso=0)
        carga_3a = cursos_repository.buscar_carga(_id_carga(curso, "3ro", "A"))
        _guardar_notas(carga_3a, base_3a, (4,), {"Práctica 1": 0}, ajuste_curso=0)


def _demo_aula_virtual() -> None:
    """Materiales, tareas (con entregas) y clases virtuales en los cursos de María y de 1ro A."""
    com_3a = _id_carga("Comunicación", "3ro", "A")
    cyt_3a = _id_carga("Ciencia y Tecnología", "3ro", "A")
    mat_3a = _id_carga("Matemática", "3ro", "A")
    mat_1a = _id_carga("Matemática", "1ro", "A")

    materiales = [   # (carga, título, descripción, enlace, bimestre)
        (com_3a, "Plan lector: El caballero Carmelo", "Cuento completo de Abraham Valdelomar.",
         "https://example.com/caballero-carmelo.pdf", 4),
        (com_3a, "Guía para escribir un ensayo", "Estructura: introducción, desarrollo y conclusión.",
         "https://example.com/guia-ensayo.pdf", 4),
        (cyt_3a, "La célula: partes y funciones", "Infografía y video de repaso.",
         "https://example.com/la-celula", 3),
        (cyt_3a, "Guía de laboratorio: densidad", "Materiales y pasos del experimento.",
         "https://example.com/lab-densidad.pdf", 4),
        (mat_3a, "Funciones lineales", "Teoría, gráficas y ejercicios resueltos.",
         "https://example.com/funciones-lineales.pdf", 4),
        (mat_1a, "Fracciones equivalentes", "Ficha de práctica con 15 ejercicios.",
         "https://example.com/fracciones.pdf", 4),
    ]
    for carga, titulo, descripcion, enlace, bimestre in materiales:
        insertar("""INSERT INTO material_clase (id_carga_academica, titulo, descripcion, archivo_url, bimestre)
                    VALUES (%s, %s, %s, %s, %s)""", (carga, titulo, descripcion, enlace, bimestre))

    tareas = [   # (carga, título, descripción, publicada hace N días, vence en N días)
        (com_3a, MARCA_DEMO_COMPLETA, "Ensayo de 2 páginas sobre un lugar o una persona especial.", -2, 5),
        (com_3a, "Ficha de lectura: El caballero Carmelo", "Completa la ficha: personajes, tema y mensaje.", -14, -6),
        (cyt_3a, "Informe de laboratorio: densidad", "Informe con tus mediciones y conclusiones.", -1, 9),
        (cyt_3a, "Cuestionario: la célula", "Responde las 12 preguntas del cuestionario.", -16, -12),
        (mat_1a, "Fracciones: ejercicios", "Resolver la ficha de fracciones equivalentes.", -1, 3),
    ]
    for carga, titulo, descripcion, publicada, vence in tareas:
        insertar("""
            INSERT INTO tarea (id_carga_academica, titulo, descripcion, fecha_publicacion, fecha_entrega,
                               bimestre, estado, tipo_evaluacion, peso)
            VALUES (%s, %s, %s, %s, %s, 4, 'ACTIVO', 'TAREA', 0)
        """, (carga, titulo, descripcion, _cuando(publicada, "08:00"), _cuando(vence, "23:59")))

    entregas = [   # (tarea, alumno, enviada hace N días, nota, comentario del docente)
        ("Ficha de lectura: El caballero Carmelo", "ALU-33333333", -8, 18, "Muy buena identificación del tema."),
        ("Ficha de lectura: El caballero Carmelo", "ALU-73333333", -9, 19, "¡Excelente análisis!"),
        ("Ficha de lectura: El caballero Carmelo", "ALU-75555555", -7, 14, "Completa la sección del mensaje."),
        ("Ficha de lectura: El caballero Carmelo", "ALU-71111111", -7, None, None),   # por calificar
        ("Ficha de lectura: El caballero Carmelo", "ALU-74444444", -4, None, None),   # tarde, por calificar
        ("Cuestionario: la célula", "ALU-33333333", -13, 16, "Bien, repasa la mitocondria."),
        ("Cuestionario: la célula", "ALU-72222222", -13, 11, "Faltaron 4 preguntas."),
        ("Cuestionario: la célula", "ALU-79999999", -12, None, None),                 # por calificar
        (MARCA_DEMO_COMPLETA, "ALU-73333333", -1, None, None),                        # por calificar
        ("Proyecto: sistemas de ecuaciones", "ALU-73333333", -2, None, None),         # por calificar (Carlos)
        ("Proyecto: sistemas de ecuaciones", "ALU-76666666", -1, None, None),
    ]
    for titulo, username, enviada, nota, comentario in entregas:
        id_tarea = _id_tarea(titulo)
        insertar("""
            INSERT INTO entrega_tarea (id_tarea, id_alumno, archivo_url, fecha_envio, calificacion,
                                       retroalimentacion_docente)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_tarea, _id_alumno(username), f"https://drive.google.com/{username.lower()}-tarea-{id_tarea}",
              _cuando(enviada, "19:00"), nota, comentario))

    clases = [   # (carga, tema, en N días, hora)
        (mat_3a, "Funciones lineales: resolución de dudas", 1, "16:00"),
        (com_3a, "Taller de redacción del ensayo", 2, "15:00"),
        (cyt_3a, "Laboratorio virtual: densidad", 4, "16:30"),
        (mat_1a, "Repaso de fracciones", 3, "15:30"),
        (com_3a, "Análisis de El caballero Carmelo", -5, "15:00"),
    ]
    for carga, tema, dias, hora in clases:
        insertar("""INSERT INTO clase_virtual (id_carga_academica, tema, fecha, enlace)
                    VALUES (%s, %s, %s, 'https://meet.google.com/amv-demo-clase')""",
                 (carga, tema, _cuando(dias, hora)))


def _demo_asistencia() -> None:
    """Asistencia de los últimos 8 días hábiles en 3ro A y 1ro A. HOY queda pendiente,
    para que el auxiliar pueda registrarla durante la demostración."""
    # Un texto por día con el estado de los 8 alumnos de 3ro A (orden de ALUMNOS_3RO_A).
    # J = falta justificada, j = tardanza justificada (se guarda J con estado_original T).
    estados_3a = ["PPPPPPPP", "PjPPPPPF", "PPFPPPPP", "PPPTPPPP",
                  "PPPPPJPP", "TPPPFPPP", "PPPPPPTP", "PPFPPPPP"]
    estados_mateo = "PPTPPPPP"
    for i, dia in enumerate(_dias_habiles_anteriores(8)):
        del_dia = list(zip(ALUMNOS_3RO_A, estados_3a[i])) + [("ALU-44444444", estados_mateo[i])]
        for username, estado in del_dia:
            id_matricula = _id_matricula(username)
            if _id("SELECT COUNT(*) FROM asistencia WHERE id_matricula = %s AND fecha = %s",
                   (id_matricula, dia)):
                continue
            estado, original = {"J": ("J", "F"), "j": ("J", "T")}.get(estado, (estado, None))
            insertar("INSERT INTO asistencia (id_matricula, fecha, estado, estado_original) "
                     "VALUES (%s, %s, %s, %s)", (id_matricula, dia, estado, original))


def _demo_conducta() -> None:
    """Reportes de varios alumnos: uno de HOY, uno grave y uno ANULADO."""
    auxiliar = _id_usuario("AUX-77777777")
    reportes = [   # (alumno, falta, hace N días, hora, descripción)
        ("ALU-71111111", "Tardanza injustificada", 0, "07:55", "Llegó 15 minutos tarde a la formación."),
        ("ALU-72222222", "Falta de respeto a un compañero", -3, "11:00",
         "Insultó a un compañero durante la clase de Matemática."),
        ("ALU-76666666", "No portar el uniforme completo", -7, "07:50", "Vino con zapatillas de color."),
        ("ALU-44444444", "Tardanza injustificada", -2, "08:05", "Llegó después del inicio de clases."),
    ]
    for username, falta, dias, hora, descripcion in reportes:
        insertar("""
            INSERT INTO reporte_conducta (id_alumno, id_nivel_conducta, registrado_por, fecha_reporte,
                                          descripcion_suceso, estado)
            VALUES (%s, %s, %s, %s, %s, 'REGISTRADO')
        """, (_id_alumno(username), _id_falta(falta), auxiliar, _cuando(dias, hora), descripcion))

    # Un reporte anulado (en la app se ve tachado, con el motivo).
    insertar("""
        INSERT INTO reporte_conducta (id_alumno, id_nivel_conducta, registrado_por, fecha_reporte,
                                      descripcion_suceso, estado, motivo_anulacion, anulado_por,
                                      fecha_anulacion)
        VALUES (%s, %s, %s, %s, 'Usaba el celular durante la clase de Ciencia.', 'ANULADO',
                'Tenía permiso de la docente para usar la calculadora del celular.', %s, %s)
    """, (_id_alumno("ALU-74444444"), _id_falta("Uso del celular en clase"), auxiliar,
          _cuando(-5, "10:30"), auxiliar, _cuando(-5, "12:00")))


def _demo_citas() -> None:
    """Una cita HOY, una en dos días, una solicitud nueva, una cancelada y un seguimiento."""
    psicologo = _id("""SELECT p.id_psicologo FROM psicologo p JOIN usuario u ON u.id_usuario = p.id_usuario
                       WHERE u.username = 'PSI-88888888'""")
    # (alumno, motivo, disponibilidad, solicitada hace N días, fecha de la cita, estado,
    #  observación, motivo de cancelación)
    citas = [
        ("ALU-71111111", "Me cuesta llegar temprano porque cuido a mi hermano", "Mañanas",
         -3, _cuando(0, "11:30"), "PROGRAMADA", None, None),
        ("ALU-72222222", "Tuve un problema con un compañero y quiero arreglarlo", "Después del recreo",
         -2, _cuando(2, "10:00"), "PROGRAMADA", None, None),
        ("ALU-73333333", "Me siento muy estresada por los exámenes", "Viernes por la tarde",
         -1, None, "PENDIENTE", None, None),
        ("ALU-76666666", "Quiero orientación para organizar mis tareas", "Lunes",
         -9, _cuando(-4, "09:00"), "CANCELADA", None,
         "El estudiante viajó con su familia; se reprogramará a su regreso."),
        ("ALU-33333333", "Seguimiento de concentración en clase", "Mañanas",
         -14, _cuando(-11, "10:00"), "ATENDIDA",
         "Mejoró su organización y mantiene su horario de estudio. Nuevo seguimiento en diciembre.", None),
    ]
    for username, motivo, disponibilidad, solicitada, fecha_cita, estado, observacion, cancelacion in citas:
        id_alumno = _id_alumno(username)
        activas = _id("""SELECT COUNT(*) FROM cita_psicologia
                         WHERE id_alumno = %s AND estado IN ('PENDIENTE', 'PROGRAMADA')""", (id_alumno,))
        if activas and estado in ("PENDIENTE", "PROGRAMADA"):
            continue    # regla del colegio: solo una cita activa por alumno
        insertar("""
            INSERT INTO cita_psicologia (id_alumno, id_psicologo, motivo, disponibilidad, fecha_cita, estado,
                                         observacion, motivo_cancelacion, fecha_solicitud)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_alumno, None if estado == "PENDIENTE" else psicologo, motivo, disponibilidad,
              fecha_cita, estado, observacion, cancelacion, _cuando(solicitada, "08:30")))


def _conversacion(usuario_a: str, usuario_b: str, mensajes: list) -> None:
    """Crea una conversación con sus mensajes: [(remitente, texto, hace N días, hora, leído)]."""
    a, b = _id_usuario(usuario_a), _id_usuario(usuario_b)
    ultimo = mensajes[-1]
    id_conversacion = insertar("""
        INSERT INTO conversacion (usuario1_id, usuario2_id, ultimo_mensaje, fecha_actualizacion)
        VALUES (%s, %s, %s, %s)
    """, (min(a, b), max(a, b), ultimo[1], _cuando(ultimo[2], ultimo[3])))
    for remitente, texto, dias, hora, leido in mensajes:
        insertar("""INSERT INTO mensaje (id_conversacion, remitente_id, contenido, leido, fecha_envio)
                    VALUES (%s, %s, %s, %s, %s)""",
                 (id_conversacion, _id_usuario(remitente), texto, leido, _cuando(dias, hora)))


def _demo_mensajes() -> None:
    """Conversaciones para todos los roles; cada uno tiene al menos un mensaje sin leer."""
    _conversacion("ALU-33333333", "DOC-66666666", [
        ("ALU-33333333", "Profesora, ¿el ensayo puede ser sobre mi abuela?", -1, "18:20", 1),
        ("DOC-66666666", "¡Claro, Lucía! Puede ser sobre una persona especial. Mínimo 2 páginas.", -1, "19:05", 0),
    ])
    _conversacion("ALU-71111111", "PSI-88888888", [
        ("PSI-88888888", "Hola, Sofía. Tu cita quedó para hoy a las 11:30 en el tópico.", -1, "09:00", 1),
        ("ALU-71111111", "Gracias, ahí estaré.", -1, "09:30", 1),
    ])
    _conversacion("AUX-77777777", "DOC-22222222", [
        ("AUX-77777777", "Profesor, Diego tuvo un reporte por faltarle el respeto a un compañero en su clase.",
         -3, "12:00", 1),
        ("DOC-22222222", "Gracias, Jorge. Conversaré con él y con su apoderado.", -3, "12:30", 0),
    ])
    _conversacion("ADM-11111111", "DOC-22222222", [
        ("ADM-11111111", "Carlos, recuerda cerrar el 3.er bimestre de Matemática esta semana.", 0, "08:00", 0),
    ])
    _conversacion("ALU-73333333", "PSI-88888888", [
        ("ALU-73333333", "Hola, envié una solicitud de cita. ¿Cuándo podría atenderme?", -1, "20:00", 0),
    ])
    _conversacion("ALU-44444444", "DOC-22222222", [
        ("ALU-44444444", "Profesor, ¿las fracciones se simplifican al final?", -1, "17:10", 1),
        ("DOC-22222222", "Sí, Mateo. Siempre deja el resultado en su mínima expresión.", -1, "17:45", 0),
    ])


def _demo_notificaciones() -> None:
    """Avisos sin leer para cada rol (en la app real los crean los services)."""
    ensayo = _id_tarea(MARCA_DEMO_COMPLETA)
    ficha = _id_tarea("Ficha de lectura: El caballero Carmelo")
    fracciones = _id_tarea("Fracciones: ejercicios")
    clase = _id("SELECT MAX(id_clase_virtual) FROM clase_virtual WHERE tema = 'Funciones lineales: resolución de dudas'")

    def ultima_cita(username):
        return _id("SELECT MAX(id_cita) FROM cita_psicologia WHERE id_alumno = %s", (_id_alumno(username),))

    def conversacion_entre(usuario_a, usuario_b):
        a, b = _id_usuario(usuario_a), _id_usuario(usuario_b)
        return _id("SELECT id_conversacion FROM conversacion WHERE usuario1_id = %s AND usuario2_id = %s",
                   (min(a, b), max(a, b)))

    avisos = [   # (usuario, tipo, título, mensaje, referencia, leída, hace N días, hora)
        ("ALU-33333333", "CLASE", "Nueva clase virtual de Matemática",
         "Funciones lineales: resolución de dudas · mañana 16:00", clase, 0, -1, "10:00"),
        ("ALU-33333333", "MENSAJE", "Mensaje de María Salazar Vega",
         "¡Claro, Lucía! Puede ser sobre una persona especial.",
         conversacion_entre("ALU-33333333", "DOC-66666666"), 0, -1, "19:05"),
        ("ALU-33333333", "CALIFICACION", "Tu tarea fue calificada",
         "Ficha de lectura: El caballero Carmelo: 18", ficha, 1, -6, "09:00"),
        ("ALU-71111111", "CITA", "Cita programada", "Tu cita con psicología es hoy a las 11:30",
         ultima_cita("ALU-71111111"), 0, -1, "09:00"),
        ("ALU-71111111", "CONDUCTA", "Nuevo reporte de conducta", "Tardanza injustificada (−1 punto)",
         None, 0, 0, "08:00"),
        ("ALU-72222222", "CITA", "Cita programada", "Tu cita con psicología es en dos días a las 10:00",
         ultima_cita("ALU-72222222"), 0, -2, "12:00"),
        ("ALU-72222222", "CONDUCTA", "Nuevo reporte de conducta", "Falta de respeto a un compañero (−5 puntos)",
         None, 1, -3, "11:05"),
        ("ALU-73333333", "CALIFICACION", "Tu tarea fue calificada",
         "Ficha de lectura: El caballero Carmelo: 19", ficha, 0, -6, "09:00"),
        ("ALU-44444444", "TAREA", "Nueva tarea de Matemática", "Fracciones: ejercicios · entrega en 3 días",
         fracciones, 0, -1, "08:00"),
        ("DOC-22222222", "MENSAJE", "Mensaje de Ana Torres Ruiz",
         "Carlos, recuerda cerrar el 3.er bimestre de Matemática esta semana.",
         conversacion_entre("ADM-11111111", "DOC-22222222"), 0, 0, "08:00"),
        ("AUX-77777777", "MENSAJE", "Mensaje de Carlos Mendoza Paz",
         "Gracias, Jorge. Conversaré con él y con su apoderado.",
         conversacion_entre("AUX-77777777", "DOC-22222222"), 0, -3, "12:30"),
        ("PSI-88888888", "CITA", "Nueva solicitud de cita",
         "Valeria Huamán Rojas: Me siento muy estresada por los exámenes",
         ultima_cita("ALU-73333333"), 0, -1, "08:30"),
        ("PSI-88888888", "MENSAJE", "Mensaje de Valeria Huamán Rojas",
         "Hola, envié una solicitud de cita. ¿Cuándo podría atenderme?",
         conversacion_entre("ALU-73333333", "PSI-88888888"), 0, -1, "20:00"),
        ("ADM-11111111", "LIBRETA", "Bimestre cerrado",
         "Matemática 3ro A: el 2.º bimestre ya está en la libreta", None, 1, -10, "18:00"),
    ]
    # La nueva tarea de Comunicación se avisó a toda la sección.
    avisos += [(username, "TAREA", "Nueva tarea de Comunicación",
                f"{MARCA_DEMO_COMPLETA} · entrega en 5 días", ensayo, 0, -2, "08:00")
               for username in ALUMNOS_3RO_A]
    for username, tipo, titulo, mensaje, referencia, leida, dias, hora in avisos:
        insertar("""
            INSERT INTO notificacion (id_usuario, tipo, titulo, mensaje, id_referencia, leida, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (_id_usuario(username), tipo, titulo, mensaje, referencia, leida, _cuando(dias, hora)))
