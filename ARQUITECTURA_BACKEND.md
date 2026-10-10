# Arquitectura del backend

Esta guía explica, con palabras sencillas, cómo está organizado el backend del
Colegio Amancio Varona y qué ocurre desde que el frontend envía una petición
hasta que recibe una respuesta.

> **En pocas palabras:** es una API construida con FastAPI y Python. Recibe
> peticiones del frontend, valida los datos, ejecuta las reglas del colegio y
> consulta o modifica una base de datos MySQL.

## 1. El recorrido de una petición

```text
Frontend (navegador)
        │
        │ HTTP/JSON; en algunos casos WebSocket
        ▼
main.py
  ├─ configura CORS, compresión y límites de petición
  ├─ comprueba la configuración al arrancar
  └─ conecta la URL con el router correspondiente
        │
        ▼
Router del módulo
  ├─ comprueba la sesión y los permisos si hacen falta
  ├─ valida la entrada y define el formato de salida
  └─ ejecuta la operación (a veces directamente, a veces usando un service)
        │
        ├──────────────► Base de datos MySQL (SQLAlchemy)
        ├──────────────► Archivos en /media
        └──────────────► Servicios externos, cuando corresponde
        │
        ▼
Respuesta JSON (o archivo) para el frontend
```

Una analogía útil:

- **`main.py`** es la recepción del colegio: prepara el edificio y dirige cada
  visita al área correcta.
- **El router** es quien recibe una solicitud y sabe qué operación corresponde.
- **El schema** es el formulario: define qué datos se aceptan y cómo se
  devuelven.
- **El service**, cuando existe, contiene reglas de negocio reutilizables.
- **El model** representa una tabla de la base de datos.
- **`database.py`** presta y cierra la conexión con la base de datos.

No todos los módulos separan estas responsabilidades del mismo modo. Algunos
routers contienen bastante lógica y consultas; otros cuentan con archivos
`service.py` para separar parte de esa lógica.

## 2. Carpetas principales

| Ubicación | Para qué sirve |
| --- | --- |
| `main.py` | Punto de entrada. Configura FastAPI, registra routers, monta archivos estáticos y declara el WebSocket general. |
| `app/core/` | Configuración del entorno y utilidades compartidas, por ejemplo JWT, contraseñas, permisos, correo y archivos. |
| `app/db/` | Creación del motor SQLAlchemy, sesiones y base común para los modelos. |
| `app/modules/` | Funciones agrupadas por área del sistema escolar. Normalmente cada área tiene routers, modelos y schemas; algunas también tienen servicios. |


## 4. Cómo se conectan los datos con MySQL

En [`app/db/database.py`](./app/db/database.py):

- SQLAlchemy crea el motor de conexión para MySQL mediante PyMySQL.
- `SessionLocal` fabrica una sesión de base de datos para trabajar durante una
  petición.
- `get_db()` entrega esa sesión mediante la inyección de dependencias de
  FastAPI y la cierra al terminar, incluso si la petición falla.
- Los modelos declarativos describen las tablas y sus relaciones.

En un router, `db: Session = Depends(get_db)` pide una sesión sin tener que
abrirla y cerrarla manualmente en cada ruta.

## 5. Validación y responsabilidades

FastAPI utiliza los schemas de Pydantic para revisar los datos que llegan y
para estructurar algunas respuestas. Si una ruta declara un `response_model`,
FastAPI también ayuda a mantener consistente el formato que recibe el frontend.

Los modelos de SQLAlchemy representan los datos persistentes. Los services
agrupan operaciones y reglas que conviene reutilizar. Por ejemplo,
[`app/modules/finance/service.py`](./app/modules/finance/service.py) contiene
operaciones de negocio relacionadas con pensiones, pagos y moras.

La separación no es uniforme: en áreas como matrícula, el router realiza
consultas y algunas reglas directamente. Esto funciona, pero es un punto que
puede mejorarse gradualmente (ver recomendaciones).

## 6. Inicio de sesión y autorización

El flujo de inicio de sesión de `POST /usuarios/login` es, simplificado:

1. Revisa si hay un bloqueo temporal por intentos fallidos.
2. Busca el usuario en la base de datos.
3. Compara la contraseña recibida con su hash.
4. Rechaza la cuenta si está desactivada.
5. Registra el resultado del intento de inicio de sesión.
6. Si corresponde, obtiene y normaliza los permisos del administrador.
7. Firma un JWT y devuelve datos de sesión. También lo coloca en la cookie
   `authToken` con `HttpOnly`; las opciones `Secure` y `SameSite` cambian según
   el entorno.

Para las siguientes solicitudes, `get_current_user` busca el JWT primero en el
encabezado HTTP de autorización y, si no está, en la cookie `authToken`.
`require_roles(...)` limita el acceso por rol y
`requiere_permiso(...)` permite comprobar permisos más específicos.

En general, una ruta puede requerir autenticación, rol y/o permiso. No todas
las rutas exigen lo mismo: depende de las dependencias declaradas en cada
router.

## 7. Ejemplo concreto: crear una matrícula

Al recibir `POST /enrollment/matriculas/`:

1. FastAPI encuentra la ruta gracias al router de matrícula registrado en
   `main.py`.
2. Valida el cuerpo de la solicitud con `MatriculaCreate`.
3. Comprueba que haya una sesión válida, que el usuario tenga el rol requerido
   y que posea el permiso definido para esa operación.
4. La ruta consulta si ya existe una matrícula para el alumno y el año escolar.
5. Si ya existe, responde con un error HTTP. Si no, crea el registro, confirma
   la transacción y actualiza el objeto para devolverlo.
6. FastAPI convierte el resultado al schema `MatriculaResponse`.

Este ejemplo también muestra que la validación del cuerpo, la autorización y
la escritura en la base de datos son pasos distintos.

## 8. Archivos, tiempo real y servicios externos

- **Archivos:** `main.py` publica el directorio configurado como `/media`. El
  directorio predeterminado es `media` dentro del backend, pero puede
  configurarse fuera del código. Los archivos subidos no son lo mismo que los
  registros guardados en MySQL.
- **WebSocket:** existe `/ws/{user_id}` para mantener una conexión en tiempo
  real. El administrador de conexiones guarda las conexiones en memoria del
  proceso. Por eso el código advierte que esta solución requiere un solo
  worker; con varios workers, cada proceso tendría una lista distinta.
- **Chatbot:** la configuración y dependencias contemplan servicios externos
  como Google y Pinecone. Para leer ciertos PDF escaneados también se usan
  herramientas OCR del sistema operativo.
- **Correo:** hay configuración para enviar notificaciones mediante SMTP.

## 9. Configuración y ejecución local

La plantilla de variables es [`.env.example`](./.env.example). Debe usarse como
referencia para configurar `.env`; no se deben publicar credenciales reales.
Algunas variables importantes son:

- Base de datos: `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME`.
- Seguridad: `SECRET_KEY`, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Entorno y frontend: `ENTORNO`, `ALLOWED_ORIGINS`.
- Funciones externas: claves del chatbot y parámetros SMTP, cuando se usan.

`requirements.txt` documenta las dependencias. Sus instrucciones indican el
uso de Python 3.12. Con el entorno virtual y dependencias instalados, el
servidor de desarrollo normalmente se inicia con:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

La base debe estar accesible y las variables requeridas definidas antes de
iniciar el proceso.

## 10. ¿Se puede mejorar?

Sí. La arquitectura modular ya da una base útil para mantener el sistema; las
mejoras más prácticas se pueden hacer por etapas:

### Prioridad alta: claridad y consistencia

1. **Actualizar el README:** el `README.md` actual incluye ejemplos de carpetas
   y áreas que no coinciden exactamente con los módulos reales. Conviene dejar
   allí una introducción breve y enlazar este documento como guía vigente.
2. **Separar reglas de negocio de routers grandes:** mover reglas y operaciones
   repetidas a `service.py`, empezando por las rutas más extensas o que ya
   mezclan muchas consultas, decisiones y escrituras. El router quedaría
   centrado en HTTP, validaciones y dependencias.
3. **Estandarizar las transacciones:** definir con claridad dónde se hace
   `commit`, cómo se hace `rollback` si falla una operación y si los services
   reciben una sesión o son responsables de confirmar cambios. Esto evita
   estados parciales y facilita las pruebas.
4. **Unificar errores y respuestas:** reutilizar convenciones claras para
   errores HTTP y mensajes, evitando que operaciones similares respondan de
   formas distintas.

### Prioridad alta: operación y protección

5. **Proteger y probar el WebSocket:** el endpoint toma `user_id` de la URL.
   Conviene autenticar la conexión y comprobar que el usuario pueda conectarse
   con ese identificador. Si en el futuro se necesitan varios workers, mover
   la coordinación de conexiones/mensajes a un sistema compartido, por ejemplo
   Redis Pub/Sub.
6. **Revisar qué archivos se publican en `/media`:** los archivos estáticos
   servidos directamente no pasan por las dependencias de permisos de los
   routers. Si allí puede haber documentos privados de alumnos o familias,
   separar contenido público y privado, y servir lo privado con autorización o
   enlaces temporales.
7. **Agregar pruebas automatizadas de rutas y servicios:** cubrir login,
   permisos, matrícula y operaciones financieras con una base de prueba. En la
   raíz se encuentran scripts de prueba puntuales, pero no se identifica una
   suite central de pruebas automatizadas.

### Prioridad media: cambios de datos y crecimiento

8. **Formalizar migraciones de base de datos:** `requirements.txt` incluye
   Alembic, pero no se ve una estructura estándar de migraciones en el
   repositorio. Añadirla permitiría revisar y aplicar cambios de esquema de
   forma repetible, en vez de depender de cambios manuales o scripts aislados.
9. **Añadir monitoreo estructurado:** registrar errores y operaciones
   importantes con logs estructurados, y exponer comprobaciones de salud para
   distinguir si falla la API, MySQL u otro servicio externo.
10. **Planificar el almacenamiento de archivos:** si el backend crece o se
    despliega en más de una instancia, usar almacenamiento persistente
    compartido (por ejemplo, almacenamiento de objetos) en lugar del disco
    local de una instancia.

### Una forma segura de empezar

No hace falta reescribir todo el backend. Una secuencia de bajo riesgo sería:

1. Documentar una operación existente, por ejemplo matrícula o login.
2. Añadir pruebas para el comportamiento actual.
3. Extraer una regla concreta del router a un service.
4. Ejecutar las pruebas y comparar las respuestas antes y después.
5. Repetir el proceso por módulo, sin mezclar refactorizaciones grandes.

Así se mejora la estructura sin cambiar de golpe la manera en que funciona el
frontend.
