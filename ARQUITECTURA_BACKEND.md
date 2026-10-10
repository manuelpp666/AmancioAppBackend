# Arquitectura del backend móvil

Este backend FastAPI sirve a la aplicación móvil del Campus AV. El alcance
completo está descrito en
[`alcance_del_proyecto.md`](./alcance_del_proyecto.md).

## Recorrido de una petición

```text
Aplicación móvil
        │ HTTP/JSON o WebSocket
        ▼
main.py
  ├─ configura CORS, compresión y límites de petición
  ├─ comprueba la configuración al arrancar
  └─ publica únicamente las rutas permitidas para la app móvil
        │
        ▼
Router ── valida la sesión, los permisos y los datos de entrada
        │
        ├── MySQL mediante SQLAlchemy
        ├── archivos de cursos, tareas y entregas
        └── correo o WebSocket cuando la función lo requiere
```

`main.py` mantiene una lista explícita de métodos y rutas móviles para cada
router. Por eso, que una ruta exista en un módulo no significa que esté
disponible en esta API: las operaciones financieras, de personal y estructura
administrativa, admisión, verano y contenido web no se registran.

## Funciones publicadas

- Autenticación, permisos del usuario, perfil y cambio obligatorio de
  contraseña.
- Consultas académicas y libreta del estudiante; registro y consulta de notas
  y asistencia.
- Catálogo, reportes y notas de conducta; citas, agenda e historial de
  psicología.
- Horarios de estudiantes y docentes.
- Materiales, clases virtuales, tareas, entregas y mensajería.
- Consulta del estado de matrícula del año activo, sin deuda, pagos,
  renovación ni otros datos económicos.

Las consultas de estado validan la sesión y limitan el acceso al propio usuario
o al rol autorizado. La app no recibe permisos para crear matrículas, tramitar
renovaciones ni administrar personal o estructura académica.

## Datos y módulos compartidos

`app/db/database.py` crea el motor SQLAlchemy y entrega sesiones mediante
`get_db()`. Los routers usan modelos y servicios para leer o actualizar MySQL.
Algunas tablas y modelos se comparten entre las funciones móviles y los
módulos heredados del backend web; esos modelos se conservan para evitar
romper relaciones y consultas móviles. La selección de rutas en `main.py`
define lo que esta copia ofrece a sus clientes.

Los archivos se almacenan bajo `MEDIA_DIR` (por defecto `media`) y solo se
publican las carpetas `materiales_clase`, `recursos_tareas` y `entregas_tareas`.
El WebSocket
`/ws/{user_id}` y la mensajería usan conexiones en memoria; esta configuración
requiere un solo worker para que los procesos compartan las conexiones. Las
notificaciones locales, el caché y el modo offline dependen también del
cliente móvil.

## Configuración y ejecución

Usa [`.env.example`](./.env.example) como referencia y no publiques
credenciales. Se requieren, entre otras, las variables de base de datos,
seguridad y orígenes CORS. Para desarrollo con Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

La configuración se valida durante el arranque y la base de datos debe estar
accesible.
