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
| `POST /mensajes/conversaciones` | crea la conversación (si no existía) + el mensaje + el "último mensaje" + la notificación |
| `POST /tareas/<id_carga>` | la tarea + una notificación para cada alumno de la sección |
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
  schema.sql                 estructura de las 38 tablas (CREATE TABLE IF NOT EXISTS)
  amancio_app_movil.sql      exportación completa (estructura + datos de prueba)
app/
  __init__.py                create_app(): registra rutas, errores y comandos de consola
  config.py                  variables de entorno (.env)
  database.py                conexión PyMySQL por petición + funciones para ejecutar SQL
  auth.py                    JWT: crear_token(), @jwt_required("ROL"), usuario_actual()
  offline.py                 @idempotente: operaciones sin conexión (cabecera X-Id-Operacion)
  push.py                    envío de notificaciones push al celular (Expo)
  errors.py                  ApiError y manejadores → siempre {"detail": "..."}
  security.py                contraseñas con bcrypt
  utils.py                   validadores (texto, entero, fecha, enlace, lista...) y JSON
  datos_prueba.py            crear tablas, cargar datos de prueba, reiniciar la demo
  routes/                    *_routes.py       endpoints (un archivo por módulo)
  services/                  *_service.py      reglas, validaciones y transacciones
  repositories/              *_repository.py   consultas SQL
tests/                       pruebas automáticas (JWT, errores, validadores, offline, push)
postman/                     colección con las 121 peticiones de prueba
```

Cada módulo tiene sus tres archivos con el mismo nombre. Por ejemplo, asistencia:
`routes/asistencia_routes.py` → `services/asistencia_service.py` →
`repositories/asistencia_repository.py`.

## Puesta en marcha

### Primera ejecución (Windows)

Sigue estos pasos la primera vez que descargues el proyecto:

1. **Instala los requisitos:** Python y MySQL (por ejemplo, mediante XAMPP). Inicia
   MySQL desde el panel de XAMPP y confirma el puerto que está usando.
2. **Crea y activa el entorno virtual**, e instala las dependencias desde la carpeta
   del proyecto:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   Si PowerShell no permite activar el entorno, puedes omitir la activación y usar
   `.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes.
3. **Configura las variables de entorno:** crea un archivo `.env` en la raíz del
   proyecto con los datos de tu MySQL. Ajusta el puerto y la contraseña a tu
   instalación:

   ```dotenv
   DB_USER=root
   DB_PASS=
   DB_HOST=127.0.0.1:3306
   DB_NAME=amancio_app_movil
   SECRET_KEY=escribe-aqui-una-clave-aleatoria-de-al-menos-32-caracteres
   ```

   En XAMPP, `DB_PASS` suele estar vacío. En esta PC MySQL usa el puerto `3310`;
   si ese es tu caso, cambia `DB_HOST` por `127.0.0.1:3310`. `SECRET_KEY` debe
   tener al menos 32 caracteres. Opcional: `PUSH_ACTIVO=1` para que las notificaciones
   también se envíen al celular (por defecto solo se guardan en la base).
4. **Crea la base de datos y sus datos de prueba**. Elige una de estas opciones:
   - **Importar la base completa (recomendado):** abre phpMyAdmin, selecciona
     **Importar** y carga `database/amancio_app_movil.sql`.
     Otra opcion:
   - **Crear las tablas y cargar datos desde la consola:** para eso debes haber creado una nueva bd con el nombre que le pusiste a DB_NAME
     ejecuta:

     ```
     python -m flask --app run crear-tablas
     python -m flask --app run datos-prueba
     ```

     Si MySQL requiere contraseña, añade `-p` al comando `mysql`.
5. **Levanta el servidor** desde la raíz del proyecto:

   ```powershell
   python run.py
   ```

   La API quedará disponible en `http://localhost:5000`. Puedes comprobar que
   responde abriendo esa dirección en el navegador; debe devolver el estado de la API.
6. **Configura Postman:** importa `postman/AmancioApp.postman_collection.json`.
   En la colección, abre **Variables** y cambia `base_url` por la URL donde está
   corriendo la API.   

**Sesión**.

Para volver a iniciar el servidor después de esta configuración, basta con activar
el entorno virtual y ejecutar `python run.py`.

**Comandos adicionales**:

```powershell
python -m unittest discover -s tests -v   # pruebas automáticas
python -m flask --app run reiniciar-demo  # claves = DNI y bimestre 3 abierto otra vez
```

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
| ALU-73333333, ALU-74444444, ALU-75555555, ALU-76666666, ALU-79999999 | Alumno | Valeria, Andrés, Camila, Joaquín y Renata · 3ro A |

Datos académicos: año 2026 activo con 4 bimestres; secciones 1ro A, 3ro A y 3ro B de
Secundaria; 3 cursos con horario sin choques; material, una clase virtual, asistencia
de 3 fechas, 2 reportes de conducta, 2 citas (una atendida y una pendiente) y notas
de 3ro A en Matemática y Comunicación: bimestres 1 y 2 **cerrados** y 3 **abierto**; y
2 tareas de Matemática 3ro A (una vencida: Lucía entregó a tiempo y tiene nota, Sofía
entregó tarde sin nota, el resto no entregó; otra con fecha futura). 3ro A tiene **8 alumnos**.
Además: una **conversación** entre Lucía y el profesor Carlos (el último mensaje, sin leer),
**notificaciones** de ejemplo y una **operación hecha sin conexión** ya sincronizada
(la entrega de Sofía, id `demo-offline-sofia-0001`).

**Primer ingreso:** el login devuelve `debe_cambiar_password`. Si es `true`, la app
obliga a cambiar la contraseña (la inicial es el DNI) con `POST /perfil/auth/change-password`,
que la apaga. La nueva clave no puede ser el DNI.

## Endpoints (64)

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
| GET | `/asistencia/seccion/<id_seccion>/resumen?desde=<f>&hasta=<f>` | AUXILIAR, DOCENTE, ADMIN | Asistencia (reporte por fechas) |
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
| GET | `/citas/alumno/<id_alumno>` | PSICOLOGO | Citas (historial con observaciones) |
| GET | `/inicio` | JWT (cada rol ve lo suyo) | Panel de inicio |
| GET | `/mensajes/contactos` | JWT | Mensajería |
| GET | `/mensajes/conversaciones` | JWT | Mensajería |
| POST | `/mensajes/conversaciones` | JWT (a un contacto) | Mensajería (transacción) |
| GET | `/mensajes/conversaciones/<id>` | participante | Mensajería |
| POST | `/mensajes/conversaciones/<id>` | participante | Mensajería (transacción) |
| PATCH | `/mensajes/conversaciones/<id>/leido` | participante | Mensajería |
| GET | `/notificaciones?solo_no_leidas=1` | JWT | Notificaciones |
| PATCH | `/notificaciones/<id>/leida` | dueño | Notificaciones |
| PATCH | `/notificaciones/leer-todas` | JWT | Notificaciones |
| GET | `/offline/operaciones/<id_operacion>` | dueño | Sin conexión |

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
- **Mensajería:** chat entre dos usuarios. Para *iniciar* una conversación el otro debe ser
  tu contacto (403 si no): el alumno puede escribir a los docentes de su sección, a los
  auxiliares y a la psicóloga; el docente, a sus alumnos y al personal; auxiliar, psicóloga
  y admin, a cualquiera. Solo los dos participantes leen y responden (403).
- **Notificaciones:** se crean solas, dentro de la misma transacción de la acción: nueva
  tarea, entrega calificada, clase virtual, bimestre cerrado (libreta), cita programada o
  cancelada, reporte de conducta y mensaje nuevo. Si la petición sale bien y `PUSH_ACTIVO=1`,
  además se envían al celular (tokens de Expo de `/dispositivos/token`).
- **Sin conexión:** las rutas que la app puede enviar offline (entregar tarea, asistencia por
  lote, reporte de conducta, solicitar cita, registrar notas y enviar mensajes) aceptan la
  cabecera `X-Id-Operacion`. Si llega dos veces el mismo id, la segunda NO se ejecuta: se
  devuelve la respuesta guardada con la cabecera `X-Operacion-Repetida: true` (no se duplica
  nada). Mismo id de otro usuario → 409; id con formato inválido → 400.
- **Panel de inicio:** `GET /inicio` junta lo del día según el rol (clases de hoy, próximas
  tareas, últimas notas, entregas por calificar, secciones sin asistencia, citas de hoy...).

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

Importa `postman/AmancioApp.postman_collection.json` (121 peticiones). Ejecuta primero la carpeta
**Sesión** (guarda un token por rol) y luego el resto en orden, o toda la colección con
el **Runner**: cada petición comprueba su código esperado y guarda los ids que necesitan
las siguientes. Las carpetas **Notas** (cierra el bimestre 3) y **Primer ingreso** (cambia la
clave de Mateo) solo se pueden ejecutar una vez; para repetirlas: `flask --app run reiniciar-demo`.
Carpetas de los módulos nuevos: **Mensajería**, **Notificaciones**, **Panel de inicio** y
**Sin conexión (offline)** (envía el mismo mensaje dos veces con el mismo `X-Id-Operacion`
y comprueba que no se duplica).

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
- **Notificaciones push con Expo** (`app/push.py`): la app está hecha con Expo, así que
  basta con enviar el token del celular al servicio de Expo (sin credenciales de Firebase).
  Se envían en segundo plano y nunca rompen la respuesta: la notificación ya quedó en la base.
- **Idempotencia para el modo sin conexión** (`app/offline.py`): tabla `operacion_offline`
  con el id de cada operación y su respuesta.


**Datos mínimos de la demostración** (sección 13 de la propuesta): incluidos en los datos
de prueba (8 alumnos en 3ro A, una conversación con mensajes y una operación hecha sin conexión).

## Estado de verificación

- 22 pruebas automáticas (JWT, errores, validadores, id de operación offline y armado del push).
- La colección de Postman completa (121 peticiones) pasa contra una base creada desde cero.
- La base se puede crear de cero con `crear-tablas` + `datos-prueba`, o importando
  `database/amancio_app_movil.sql`; ambos caminos se probaron en bases temporales.
