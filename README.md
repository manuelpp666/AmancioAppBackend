# Campus AV Móvil — API (Flask + JWT)

API REST para la app móvil del Campus Virtual del colegio Amancio Varona.
Reutiliza la **base MySQL del campus web** (los modelos SQLAlchemy vienen del backend
original) y expone solo lo que la app móvil necesita.

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
  utils.py                 validación de JSON, fechas ISO, extraer_dni
  models/                  tablas del campus web (copiadas) + dispositivo_push (nueva)
  services/                lógica reutilizable (bloqueo de login, contacto, interruptores)
  blueprints/              rutas, un archivo por módulo
tests/                     pruebas sin base de datos (JWT, errores, utilidades)
```

## Puesta en marcha

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env        # rellena DB_* y SECRET_KEY
python run.py               # http://localhost:5000
flask --app run crear-tabla-dispositivos   # una sola vez: crea la tabla nueva
python -m unittest discover -s tests -v    # pruebas
```

## Endpoints de la Fase 1

| Método | Ruta | Acceso | Módulo |
|---|---|---|---|
| POST | `/usuarios/login` | público | 1 |
| GET | `/usuarios/mis-permisos` | JWT | 1 |
| POST | `/usuarios/logout` | JWT | 1 / 12 |
| GET | `/perfil/mi-perfil/<username>` | dueño o ADMIN | 10 |
| PATCH | `/perfil/contacto/<username>` | dueño | 10 |
| PATCH | `/perfil/alumno/<username>/direccion` | ALUMNO | 10 |
| PATCH | `/perfil/alumno/<username>/medicos` | ALUMNO | 10 |
| POST | `/perfil/auth/change-password` | JWT | 1 |
| GET | `/perfil/auth/primer-ingreso` | JWT | 1 |
| POST | `/perfil/auth/registrar-correo` | JWT | 1 |
| POST / DELETE | `/dispositivos/token` | JWT | 12 |
| GET | `/` | público (salud) | — |

Probar el login:

```bash
curl -X POST http://localhost:5000/usuarios/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ALU-12345678","password":"12345678"}'
# luego:  -H "Authorization: Bearer <access_token>"
```

## Decisiones

- **PyJWT directo + decorador propio** (en vez de Flask-JWT-Extended): son ~60 líneas
  legibles en `app/auth.py`, fáciles de explicar en la sustentación. El token lleva
  `sub`, `id`, `rol`, `iat`, `exp` (igual que el backend original).
- **Errores siempre en JSON con la clave `detail`**, para que el interceptor de la app
  lea el mensaje de un solo sitio. Códigos usados: 400, 401, 403, 404, 429, 500.
- **Bloqueo de fuerza bruta conservado**: 5 fallos por usuario o 20 por IP en 15 min → 429.
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
| 2 | Horario, Notas/libreta, Asistencia | `horario/router.py`, `management/router.py`, `academic/router_libreta.py` |
| 3 | Conducta, Citas de psicología | `behavior/router.py` |
| 4 | Aula virtual, Mensajería, Notificaciones | `virtual/router.py`, `management/router.py` |
| 5 | Offline (`id_operacion` idempotente) y envío push (FCM) | nuevo |

## Estado de verificación

Probado: JWT, errores, serialización y utilidades (14 pruebas, sin base de datos);
sintaxis de todo el código; que cada import interno y cada columna usada existe.
**Aún no probado contra MySQL real**: login, perfil y dispositivos necesitan una base
con datos de prueba para validarlos de extremo a extremo.
