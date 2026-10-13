# Campus AV Móvil — API (Flask + JWT)

API REST para la app móvil del Campus Virtual del colegio Amancio Varona.
Usa **su propia base MySQL** (`amancio_app_movil`), con una versión simplificada
de los modelos del campus web, y expone solo lo que la app móvil necesita.

## Estructura

```
run.py                     punto de entrada (python run.py / gunicorn run:app)
app/
  __init__.py              create_app(): registra blueprints, errores, zona horaria Lima
  config.py                variables de entorno
  database.py              engine + sesión por petición (scoped_session)
  auth.py                  JWT: crear_token(), @jwt_required("ROL"), usuario_actual()
  errors.py                ApiError y manejadores → siempre {"detail": "..."}
  security.py              bcrypt
  utils.py                 validación de JSON (texto, entero), fechas ISO, extraer_dni
  models/                  tablas (simplificadas del campus web) + dispositivo_push
  base_nueva.py            crear las tablas y cargar los datos de prueba
  services/                lógica reutilizable: contacto (correo/teléfono según el rol)
                           y cursos (año activo, quién puede ver o editar un curso)
  blueprints/              rutas, un archivo por módulo
tests/                     pruebas sin base de datos (JWT, errores, utilidades)
```

## Cómo funciona una petición

Ejemplo: la app pide `GET /perfil/mi-perfil/ALU-33333333` con su token.

1. **Ruta** (`blueprints/perfil_bp.py`): Flask encuentra la función `mi_perfil`.
2. **Seguridad** (`auth.py`): `@jwt_required()` lee el token de la cabecera
   `Authorization: Bearer ...`, comprueba su firma y que no haya vencido.
   Si falla → 401.
3. **Permiso**: `exigir_dueno_o_roles` deja pasar solo al dueño del perfil o a un ADMIN
   (si no → 403).
4. **Base de datos** (`models/` + `database.py`): se consulta con SQLAlchemy,
   usando clases de Python en vez de SQL a mano.
5. **Lógica** (`services/contacto.py`): el correo y teléfono del alumno se toman
   de su familiar.
6. **Respuesta**: se devuelve JSON. Si algo falla en cualquier paso, `errors.py`
   responde `{"detail": "mensaje"}` con el código adecuado.

## Puesta en marcha

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env        # rellena DB_* y SECRET_KEY
flask --app run crear-tablas    # crea las tablas que falten (no borra nada)
flask --app run datos-prueba    # usuarios de prueba (ver app/base_nueva.py)
python run.py                   # http://localhost:5000
python -m unittest discover -s tests -v    # pruebas
```

### Base local en XAMPP

En esta PC, MySQL de XAMPP (MariaDB 10.4) escucha en el puerto **3310**, no en 3306.
La base se creó una sola vez con:

```bash
C:/xampp/mysql/bin/mysql.exe -u root -h 127.0.0.1 -P 3310 -e "CREATE DATABASE amancio_app_movil CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

y en `.env`: `DB_USER=root`, `DB_PASS=` (vacío), `DB_HOST=127.0.0.1:3310`,
`DB_NAME=amancio_app_movil`. Los usuarios de prueba y su contraseña (= su DNI)
están en el encabezado de `app/base_nueva.py`.

## Endpoints (21)

| Método | Ruta | Acceso | Módulo |
|---|---|---|---|
| GET | `/` | público | Salud |
| POST | `/usuarios/login` | público | Usuarios |
| GET | `/usuarios/mis-permisos` | JWT | Usuarios |
| POST | `/usuarios/logout` | JWT | Usuarios |
| GET | `/perfil/mi-perfil/<username>` | dueño o ADMIN | Perfil |
| PATCH | `/perfil/contacto/<username>` | dueño | Perfil |
| PATCH | `/perfil/alumno/<username>/direccion` | ALUMNO dueño | Perfil |
| PATCH | `/perfil/alumno/<username>/medicos` | ALUMNO dueño | Perfil |
| POST | `/perfil/auth/change-password` | JWT | Perfil |
| POST | `/dispositivos/token` | JWT | Dispositivos |
| DELETE | `/dispositivos/token` | JWT | Dispositivos |
| GET | `/academico/anio-activo` | JWT | Catálogo académico |
| GET | `/academico/grados` | JWT | Catálogo académico |
| GET | `/academico/secciones?grado=<id>` | JWT | Catálogo académico |
| GET | `/academico/cursos` | JWT | Catálogo académico |
| GET | `/cursos/mis-cursos` | ALUMNO o DOCENTE | Mis cursos |
| GET | `/cursos/<id_carga>/alumnos` | DOCENTE del curso o ADMIN | Mis cursos |
| GET | `/material/<id_carga>?bimestre=<n>` | docente o alumnos del curso, ADMIN | Material |
| POST | `/material/<id_carga>` | DOCENTE del curso | Material |
| PUT | `/material/item/<id_material>` | DOCENTE del curso | Material |
| DELETE | `/material/item/<id_material>` | DOCENTE del curso | Material |

Un **curso** (`id_carga`) es una *carga académica*: un curso dictado por un docente
en una sección durante un año (ej. Matemática · 3ro A · 2026 · Carlos).

### Probar en Postman

Importa `postman/AmancioApp.postman_collection.json` (Import → archivo). Ejecuta
primero **Sesión / Login (alumna)** y **Sesión / Login (docente)**: guardan los
tokens solos (`token` y `token_docente`) y las demás peticiones los usan.
**Mis cursos (alumna)** guarda el id del curso de Matemática en `id_carga`, y
**Publicar material** guarda el id nuevo en `id_material`. Cada petición trae una
prueba del código esperado, así que se puede correr todo con el **Runner**.
Ojo: **Cambiar contraseña** cambia la clave de verdad (actualiza la variable
`password` después, o el siguiente login dará 401).

Probar el login con curl:

```bash
curl -X POST http://localhost:5000/usuarios/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ALU-12345678","password":"12345678"}'
# luego:  -H "Authorization: Bearer <access_token>"
```

## Versión simplificada

Para mantener el proyecto pequeño se quitaron estos modelos del campus web:
`tutor_seccion`, `exoneracion_curso`,
`exoneracion` (de matrícula), horario (`hora_lectiva`, `horario_escolar`,
`configuracion_horario`, `receso_horario`), conducta (`tipo_falta`,
`nivel_conducta`, `reporte_conducta`, `reporte_conducta_eliminado`,
`cita_psicologia`, `nota_conducta`), `clase_virtual`, `drive_clases`, y los de
login avanzado: `intento_acceso`, `solicitud_acceso` y `pagina_configuracion`.

**Un familiar por alumno.** En vez de la tabla `relacion_familiar` (varios
familiares por alumno), cada alumno apunta a un solo familiar con
`alumno.id_familiar`; un familiar sí puede tener varios hijos. El correo y el
teléfono del alumno se guardan en ese familiar, y `mi-perfil` devuelve
`"familiar": {...}` (o `null`) en lugar de una lista.

## Decisiones

- **PyJWT directo + decorador propio** (en vez de Flask-JWT-Extended): son ~60 líneas
  legibles en `app/auth.py`, fáciles de explicar en la sustentación. El token lleva
  `sub`, `id`, `rol`, `iat`, `exp` (igual que el backend original).
- **Errores siempre en JSON con la clave `detail`**, para que el interceptor de la app
  lea el mensaje de un solo sitio. Códigos usados: 400, 401, 403, 404, 500.
- **Login mínimo**: usuario + contraseña → token. Sin primer ingreso (cambio de
  clave o correo obligatorios) ni bloqueo por intentos fallidos; se pueden
  recuperar del historial de git cuando el proyecto crezca.
- Mejoras sobre el original: `mi-perfil` ya no deja ver el perfil de otro usuario;
  la URL de MySQL escapa contraseñas con caracteres especiales; JWT exige `exp`.

## Render

`render.yaml` ya define el servicio (gunicorn, 2 workers, `SECRET_KEY` autogenerada).
Rellena `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME` en el panel. Render no ofrece MySQL:
usa una MySQL externa. En el plan gratuito el servicio se duerme tras 15 min sin tráfico
(la primera petición tarda ~1 min) y el disco es efímero.

## Pendiente (fases siguientes)

| Fase | Módulos de la app | Lógica original en el backend FastAPI |
|---|---|---|
| 2 | Asistencia, Notas/libreta | `management/router.py`, `academic/router_libreta.py` |
| 3 | Tareas y entregas, Mensajería, Notificaciones | `virtual/router.py`, `management/router.py` |
| 4 | Offline (`id_operacion` idempotente) y envío push (FCM) | nuevo |

## Estado de verificación

- 15 pruebas automáticas sin base de datos (JWT, errores, utilidades).
- La colección de Postman completa (27 peticiones) pasa contra la base local de XAMPP.
- Probado también: permisos de cada curso (un docente no ve ni edita cursos ajenos,
  un alumno solo ve los cursos de su sección), validaciones del material (bimestre
  1 a 4, enlace http/https, título obligatorio).
