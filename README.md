# Campus AV Móvil — API REST (Flask + JWT + MySQL)

API REST para la app móvil del Campus Virtual del colegio Amancio Varona.
Usa su propia base MySQL (`amancio_app_movil`) con consultas **SQL escritas a mano**
(PyMySQL) y una arquitectura por capas **Route → Service → Repository → Base de datos**.

## Arquitectura

```
 App móvil ──HTTP + JWT──▶  ROUTE        recibe la petición, protege con @jwt_required,
                             │            saca los datos (JSON, URL, usuario del token)
                             ▼
                            SERVICE      valida los datos, aplica las reglas de negocio
                             │            y maneja la transacción: COMMIT o ROLLBACK
                             ▼
                            REPOSITORY   solo consultas SQL (SELECT, INSERT, UPDATE, DELETE)
                             │
                             ▼
                            MySQL
```

Ejemplo: `POST /material/4` (el docente publica un material)

1. **Route** `material_routes.publicar` → `@jwt_required("DOCENTE")` revisa el token
   y el rol, y pasa el JSON al service.
2. **Service** `material_service.publicar` → comprueba que el curso exista (404) y que
   el usuario sea su docente (403), valida título y bimestre 1–4 (400) y abre la transacción.
3. **Repository** `material_repository.crear` → `INSERT INTO material_clase (...) VALUES (%s, ...)`.
4. **Service** → `db.commit()`; si algo falla, `db.rollback()`. La route responde **201** con JSON.

### Transacciones (COMMIT / ROLLBACK)

La conexión trabaja con `autocommit=False`: nada se guarda hasta el `commit()`.
Todos los services que escriben siguen el mismo patrón:

```python
db = get_db()
try:
    repositorio.insertar(...)      # uno o varios cambios
    db.commit()                    # todo bien: se guardan
except Exception:
    db.rollback()                  # algo falló: se deshacen TODOS
    raise
```

Operaciones con **varios cambios relacionados** (donde el rollback importa de verdad):

| Endpoint | Cambios en una sola transacción |
|---|---|
| `POST /asistencia/lote` | borra la asistencia previa del día + inserta un registro por alumno |
| `POST /notas/<id_carga>` | guarda (o corrige) la nota de una evaluación para cada alumno |
| `POST /notas/<id_carga>/cerrar-bimestre` | un promedio por alumno en la libreta + el registro del cierre |
| `PATCH /perfil/contacto/<username>` (alumno sin familiar) | crea el familiar + lo enlaza al alumno |
| `flask --app run datos-prueba` | carga todos los datos de prueba |

### Consultas SQL

Todas están en `app/repositories/`. Los valores van siempre como parámetros `%s`
(nunca pegados al texto), así PyMySQL los escapa y se evita la inyección SQL:

```python
consultar_uno("SELECT * FROM usuario WHERE username = %s", (username,))
```

`app/database.py` ofrece cuatro funciones: `consultar_uno`, `consultar_todos`,
`insertar` (devuelve el id nuevo) y `ejecutar` (UPDATE/DELETE, devuelve filas afectadas).

## Estructura

```
run.py                       punto de entrada (python run.py / gunicorn run:app)
database/
  schema.sql                 estructura de las 36 tablas (CREATE TABLE IF NOT EXISTS)
  amancio_app_movil.sql      exportación completa (estructura + datos de prueba)
app/
  __init__.py                create_app(): registra rutas, errores y comandos de consola
  config.py                  variables de entorno (.env)
  database.py                conexión PyMySQL por petición + funciones para ejecutar SQL
  auth.py                    JWT: crear_token(), @jwt_required("ROL"), usuario_actual()
  errors.py                  ApiError y manejadores → siempre {"detail": "..."}
  security.py                contraseñas con bcrypt
  utils.py                   validadores (texto, entero, fecha, enlace...) y JSON
  datos_prueba.py            crear tablas, cargar datos de prueba, reiniciar la demo
  routes/                    *_routes.py       endpoints (un archivo por módulo)
  services/                  *_service.py      reglas, validaciones y transacciones
  repositories/              *_repository.py   consultas SQL
tests/                       pruebas automáticas (JWT, errores, validadores)
```

Cada módulo tiene sus tres archivos con el mismo nombre. Por ejemplo, asistencia:
`routes/asistencia_routes.py` → `services/asistencia_service.py` →
`repositories/asistencia_repository.py`.

## Puesta en marcha

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env          # rellena DB_* y SECRET_KEY
```

**Base de datos** (dos opciones):

- **Importar la exportación** (lo más rápido): en phpMyAdmin → Importar →
  `database/amancio_app_movil.sql`. Crea la base `amancio_app_movil` con todo.
- **Crearla con los comandos**:
  ```bash
  mysql -u root -e "CREATE DATABASE amancio_app_movil CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  .venv/Scripts/python -m flask --app run crear-tablas     # ejecuta database/schema.sql
  .venv/Scripts/python -m flask --app run datos-prueba     # agrega los datos de prueba
  ```

**Arrancar y probar**:

```bash
.venv/Scripts/python run.py                              # http://localhost:5000
.venv/Scripts/python -m unittest discover -s tests -v   # pruebas automáticas
.venv/Scripts/python -m flask --app run reiniciar-demo   # claves = DNI y bimestre 3 abierto otra vez
```

En esta PC, MySQL de XAMPP (MariaDB 10.4) escucha en el puerto **3310**: en `.env`
`DB_HOST=127.0.0.1:3310`, `DB_USER=root`, `DB_PASS=` (vacío), `DB_NAME=amancio_app_movil`.
En otra computadora normalmente es el **3306**.

## Usuarios de prueba

Contraseña = DNI (lo que va después del guion). Detalle en `app/datos_prueba.py`.

| Usuario | Rol | Datos |
|---|---|---|
| ADM-11111111 | Administrador | Ana |
| DOC-22222222 | Docente | Carlos · Matemática en 1ro A y 3ro A |
| DOC-66666666 | Docente | María · Comunicación y Ciencia y Tecnología |
| AUX-77777777 | Auxiliar | Jorge · registra asistencia y conducta |
| PSI-88888888 | Psicólogo | Elena · atiende las citas |
| ALU-33333333 | Alumno | Lucía · 3ro A · hermana de Mateo (misma mamá) |
| ALU-44444444 | Alumno | Mateo · 1ro A · **primer ingreso pendiente** |
| ALU-71111111 | Alumno | Sofía · 3ro A |
| ALU-72222222 | Alumno | Diego · 3ro A |

Datos académicos: año 2026 activo con 4 bimestres; secciones 1ro A, 3ro A y 3ro B de
Secundaria; 3 cursos con horario sin choques; material, una clase virtual, asistencia
de 3 fechas, 2 reportes de conducta, 2 citas (una atendida y una pendiente) y notas
de 3ro A en Matemática y Comunicación: bimestres 1 y 2 **cerrados** y 3 **abierto**; y
2 tareas de Matemática 3ro A (una vencida: Lucía entregó a tiempo y tiene nota, Sofía
entregó tarde sin nota, Diego no entregó; otra con fecha futura).

**Primer ingreso:** el login devuelve `debe_cambiar_password`. Si es `true`, la app
obliga a cambiar la contraseña (la inicial es el DNI) con `POST /perfil/auth/change-password`,
que la apaga. La nueva clave no puede ser el DNI.

## Endpoints (51)

| Método | Ruta | Acceso | Módulo |
|---|---|---|---|
| GET | `/` | público | Salud |
| POST | `/usuarios/login` | público | Usuarios |
| GET | `/usuarios/mis-permisos` | JWT | Usuarios |
| POST | `/usuarios/logout` | JWT | Usuarios |
| GET | `/perfil/mi-perfil/<username>` | dueño o ADMIN | Perfil |
| GET | `/perfil/mi-matricula` | ALUMNO | Perfil y matrícula |
| PATCH | `/perfil/contacto/<username>` | dueño | Perfil |
| PATCH | `/perfil/alumno/<username>/direccion` | ALUMNO dueño | Perfil |
| PATCH | `/perfil/alumno/<username>/medicos` | ALUMNO dueño | Perfil |
| POST | `/perfil/auth/change-password` | JWT | Perfil / primer ingreso |
| POST | `/dispositivos/token` | JWT | Dispositivos |
| DELETE | `/dispositivos/token` | JWT | Dispositivos |
| GET | `/academico/anio-activo` | JWT | Catálogo académico |
| GET | `/academico/grados` | JWT | Catálogo académico |
| GET | `/academico/secciones?grado=<id>` | JWT | Catálogo académico |
| GET | `/academico/cursos` | JWT | Catálogo académico |
| GET | `/cursos/mis-cursos` | ALUMNO, DOCENTE | Mis cursos |
| GET | `/cursos/<id_carga>/alumnos` | DOCENTE del curso, ADMIN | Mis cursos |
| GET | `/material/<id_carga>?bimestre=<n>` | docente/alumnos del curso, ADMIN | Material |
| POST | `/material/<id_carga>` | DOCENTE del curso | Material |
| PUT | `/material/item/<id_material>` | DOCENTE del curso | Material |
| DELETE | `/material/item/<id_material>` | DOCENTE del curso | Material |
| GET | `/clases/<id_carga>` | docente/alumnos del curso, ADMIN | Clases virtuales |
| POST | `/clases/<id_carga>` | DOCENTE del curso | Clases virtuales |
| PUT | `/clases/item/<id_clase>` | DOCENTE del curso | Clases virtuales |
| DELETE | `/clases/item/<id_clase>` | DOCENTE del curso | Clases virtuales |
| GET | `/tareas/<id_carga>` | docente/alumnos del curso, ADMIN | Tareas |
| POST | `/tareas/<id_carga>` | DOCENTE del curso | Tareas |
| DELETE | `/tareas/item/<id_tarea>` | DOCENTE del curso | Tareas |
| POST | `/tareas/item/<id_tarea>/entregar` | ALUMNO del curso | Tareas |
| GET | `/tareas/item/<id_tarea>/entregas` | DOCENTE del curso | Tareas |
| PATCH | `/tareas/entregas/<id_entrega>/calificar` | DOCENTE del curso | Tareas |
| GET | `/horario/mi-horario` | ALUMNO, DOCENTE | Horario |
| POST | `/asistencia/lote` | AUXILIAR | Asistencia (transacción) |
| GET | `/asistencia/seccion/<id_seccion>?fecha=<f>` | AUXILIAR, DOCENTE, ADMIN | Asistencia |
| GET | `/asistencia/mia` | ALUMNO | Asistencia |
| GET | `/notas/<id_carga>?bimestre=<n>` | DOCENTE del curso, ADMIN | Notas |
| POST | `/notas/<id_carga>` | DOCENTE del curso | Notas (transacción) |
| POST | `/notas/<id_carga>/cerrar-bimestre` | DOCENTE del curso | Notas (transacción) |
| GET | `/notas/mis-notas?bimestre=<n>` | ALUMNO | Notas |
| GET | `/notas/mi-libreta` | ALUMNO | Notas |
| GET | `/conducta/faltas` | JWT | Conducta |
| POST | `/conducta/reportes` | AUXILIAR | Conducta |
| PATCH | `/conducta/reportes/<id_reporte>/anular` | AUXILIAR, ADMIN | Conducta |
| GET | `/conducta/alumno/<id_alumno>` | el propio alumno o el personal | Conducta |
| POST | `/citas` | ALUMNO | Citas de psicología |
| GET | `/citas/mis-citas` | ALUMNO | Citas de psicología |
| GET | `/citas/agenda?fecha=<f>` | PSICOLOGO | Citas de psicología |
| PATCH | `/citas/<id_cita>/programar` | PSICOLOGO | Citas de psicología |
| PATCH | `/citas/<id_cita>/completar` | PSICOLOGO | Citas de psicología |
| PATCH | `/citas/<id_cita>/cancelar` | PSICOLOGO | Citas de psicología |

Un **curso** (`id_carga`) es una *carga académica*: un curso dictado por un docente
en una sección durante un año (ej. Matemática · 3ro A · 2026 · Carlos).

### Reglas de negocio principales

- **Asistencia por lote:** la lista debe incluir a *todos* los alumnos de la sección,
  sin repetidos ni alumnos de otra sección; estado P, T, F o J; fecha no futura.
  Registrar otra vez el mismo día reemplaza lo anterior.
- **Notas:** cada nota pertenece a una *evaluación* ("Práctica 1", "Examen"...) y va de
  0 a 20. El promedio del bimestre es el promedio simple de sus evaluaciones. Un bimestre
  **cerrado** ya no acepta notas (409); para cerrarlo, todos los alumnos deben tener al
  menos una nota (400). Al cerrar, el promedio pasa a la libreta (`resumen_nota`); con el
  4.º bimestre cerrado el curso queda APROBADO (≥ 11) o DESAPROBADO.
- **Tareas:** la fecha límite debe ser futura al publicar. El alumno entrega con un enlace
  y puede volver a entregar mientras no esté calificada (después → 409). Una entrega tardía
  se acepta pero queda marcada `fuera_de_plazo` (regla `ACEPTAR_FUERA_DE_PLAZO` en
  `tarea_service.py`). Se califica una sola vez, de 0 a 20 (409 si se repite). No se borra
  una tarea con entregas (409). Estado para el alumno: PENDIENTE, VENCIDA, ENTREGADA o CALIFICADA.
- **Conducta:** nota = 20 − puntos de los reportes vigentes del bimestre (mínimo 0);
  se calcula con SQL (`SUM` + `GROUP BY` por bimestre), no se guarda. Un reporte no se
  borra: se **anula** con motivo, quién y cuándo (anular dos veces → 409).
- **Citas:** PENDIENTE → PROGRAMADA → ATENDIDA, o CANCELADA. Solo una cita activa por
  alumno (409). Programar exige fecha futura. La observación del psicólogo no la ve el alumno.
- **Cursos:** un docente solo edita sus cursos; un alumno solo ve los de su sección.

### Códigos HTTP

Todas las respuestas de error son `{"detail": "mensaje"}`.

| Código | Cuándo |
|---|---|
| 200 / 201 | OK / creado |
| 400 | datos inválidos (falta un campo, bimestre 5, fecha mal escrita...) |
| 401 | sin token, token vencido o alterado, credenciales inválidas |
| 403 | rol sin permiso, o recurso de otro usuario |
| 404 | no existe (curso, cita, alumno...) |
| 409 | conflicto: bimestre cerrado, entrega ya calificada, tarea con entregas, ya anulado, cita activa repetida, estado que no permite la acción, dato duplicado en MySQL |
| 500 / 503 | error interno / MySQL no responde |

## Probar en Postman

La colección (`AmancioApp.postman_collection.json`, 84 peticiones) se entrega aparte,
fuera de este repositorio. Impórtala en Postman y ejecuta primero la carpeta
**Sesión** (guarda un token por rol) y luego el resto en orden, o toda la colección con
el **Runner**: cada petición comprueba su código esperado y guarda los ids que necesitan
las siguientes. Las carpetas **Notas** (cierra el bimestre 3) y **Primer ingreso** (cambia la
clave de Mateo) solo se pueden ejecutar una vez; para repetirlas: `flask --app run reiniciar-demo`.

## Entrega

- Código: este repositorio (sin el archivo `.env`, que tiene la `SECRET_KEY`).
- Base de datos: `database/amancio_app_movil.sql`.

## Decisiones

- **SQL directo con PyMySQL** (sin ORM): cada consulta se ve y se puede modificar en el
  repository. La estructura está en `database/schema.sql`.
- **PyJWT + decorador propio** `@jwt_required("ROL")`: el token lleva `sub`, `id`, `rol`,
  `iat` y `exp` (60 min).
- **Un familiar por alumno** (`alumno.id_familiar`): el correo y el teléfono del alumno
  son los de su familiar; un familiar puede tener varios hijos.
- Versión simplificada respecto al campus web: sin tutoría, exoneraciones, bloqueo por
  intentos fallidos ni varios familiares por alumno.

## Pendiente (proyecto final)

Comparado con la propuesta (*Contexto_Proyecto_Campus_AV_Movil*). El proyecto final se
presentará en FastAPI.

| Módulo de la propuesta | Estado | Qué falta |
|---|---|---|
| 1. Autenticación, sesión y roles | ✅ | — |
| 2. Panel de inicio por rol | ❌ | resumen por rol (próximas tareas, últimas notas, citas del día...) |
| 3. Notas y libreta | ✅ | (exoneraciones: quitadas en la versión simplificada) |
| 4. Asistencia | 🟡 | reporte por sección y rango de fechas |
| 5. Conducta | 🟡 | ajuste de la nota por el tutor; subir la foto (hoy es un enlace) |
| 6. Citas de psicología | 🟡 | listado de seguimiento de alumnos con reportes; historial de cambios |
| 7. Cursos y aula virtual | ✅ | (la entrega es un enlace; subir el archivo o la foto queda para FastAPI) |
| 8. Horario escolar | ✅ | — |
| 9. Mensajería interna | ❌ | contactos, conversaciones y mensajes |
| 10. Perfil y matrícula | ✅ | — |
| 11. Persistencia local y offline | ❌ | que la API reconozca un `id_operacion` repetido (idempotencia) |
| 12. Notificaciones y dispositivo | 🟡 | el token se guarda, pero falta enviar las notificaciones (FCM) |

**Datos mínimos de la demostración** (sección 13 de la propuesta) que faltan: 8 alumnos
en la sección de prueba (hay 3), una conversación con mensajes y una operación hecha
sin conexión.

## Estado de verificación

- 18 pruebas automáticas (JWT, errores, validadores de texto, números, notas, fechas y enlaces).
- La colección de Postman completa (84 peticiones) pasa contra la base de XAMPP.
- La base se puede crear de cero con `crear-tablas` + `datos-prueba`, o importando
  `database/amancio_app_movil.sql`; ambos caminos se probaron en bases temporales.
