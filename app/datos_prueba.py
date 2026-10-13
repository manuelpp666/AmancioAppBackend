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

Datos académicos: año 2026 con 4 bimestres; secciones 1ro A, 3ro A y 3ro B de
Secundaria; horario, material, una clase virtual, asistencia de 3 fechas, 2 reportes
de conducta, 2 citas (atendida y pendiente) y NOTAS de 3ro A en Matemática y
Comunicación: bimestres 1 y 2 CERRADOS (ya están en la libreta) y bimestre 3 ABIERTO.
TAREAS en Matemática de 3ro A: una vencida (Lucía entregó a tiempo y está calificada,
Sofía entregó tarde y falta calificar, Diego no entregó) y otra con fecha futura.

PRIMER INGRESO: Mateo tiene `debe_cambiar_password = 1` (aún usa su DNI y la app
le obliga a cambiarla). Las demás cuentas están marcadas como si ya la hubieran
cambiado, para poder probar sin ese paso.
"""
from datetime import date

from app.database import consultar_todos, consultar_uno, ejecutar, get_db, insertar
from app.repositories import cursos_repository, nota_repository
from app.security import get_password_hash
from app.services import nota_service

ANIO = "2026"
USUARIO_PRIMER_INGRESO = "ALU-44444444"
ARCHIVO_SCHEMA = "database/schema.sql"


# =============================================================================
# Crear las tablas
# =============================================================================

def crear_tablas() -> int:
    """Ejecuta cada sentencia de database/schema.sql. Devuelve cuántas ejecutó."""
    with open(ARCHIVO_SCHEMA, encoding="utf-8") as archivo:
        # Se quitan las líneas de comentario y se separa por ";".
        lineas = [l for l in archivo if not l.strip().startswith("--")]
    sentencias = [s.strip() for s in "".join(lineas).split(";") if s.strip()]

    db = get_db()
    with db.cursor() as cursor:
        for sentencia in sentencias:
            cursor.execute(sentencia)
    db.commit()
    return len(sentencias)


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
]


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
    en_seccion = {"ALU-33333333": ("3ro", "A"), "ALU-44444444": ("1ro", "A"),
                  "ALU-71111111": ("3ro", "A"), "ALU-72222222": ("3ro", "A")}
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
    # 3 fechas en 3ro A, con faltas y tardanzas.
    estados = {
        "2026-10-05": {"ALU-33333333": "P", "ALU-71111111": "P", "ALU-72222222": "T"},
        "2026-10-06": {"ALU-33333333": "F", "ALU-71111111": "P", "ALU-72222222": "P"},
        "2026-10-07": {"ALU-33333333": "P", "ALU-71111111": "J", "ALU-72222222": "P"},
    }
    for dia, por_alumno in estados.items():
        for username, estado in por_alumno.items():
            id_matricula = _id("SELECT id_matricula FROM matricula WHERE id_alumno = %s AND id_anio_escolar = %s",
                               (_id_alumno(username), ANIO))
            insertar("INSERT INTO asistencia (id_matricula, fecha, estado) VALUES (%s, %s, %s)",
                     (id_matricula, date.fromisoformat(dia), estado))
    return ["asistencia de 3 fechas"]


# --- 9. Notas -----------------------------------------------------------------------

def _notas() -> list[str]:
    """Notas de 3ro A en Matemática (Carlos) y Comunicación (María): dos evaluaciones
    por bimestre en los bimestres 1, 2 y 3. Se cierran el 1 y el 2; el 3 queda abierto."""
    if not _tabla_vacia("nota"):
        return []
    base = {"ALU-33333333": 16, "ALU-71111111": 13, "ALU-72222222": 10}   # nivel de cada alumno
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
