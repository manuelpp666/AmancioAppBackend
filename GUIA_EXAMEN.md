# Guía para el examen — cómo modificar la API

En el examen tienes **20 minutos** para un requerimiento que puede tocar endpoints,
Route, Service, Repository, SQL, validaciones, transacciones, errores o JWT.
Esta guía tiene el mapa del proyecto, recetas paso a paso y preguntas de sustentación.

---

## 1. Mapa rápido: ¿dónde toco?

| Si me piden… | Archivo |
|---|---|
| una URL nueva, cambiar el método o quién puede entrar (rol) | `app/routes/<modulo>_routes.py` |
| una validación, una regla de negocio, un código de error | `app/services/<modulo>_service.py` |
| una consulta SQL nueva o cambiar una consulta | `app/repositories/<modulo>_repository.py` |
| una columna o tabla nueva | `database/schema.sql` + phpMyAdmin (ALTER/CREATE) |
| un validador nuevo (texto, número, fecha, enlace) | `app/utils.py` |
| un módulo nuevo completo | los 3 archivos + registrarlo en `app/__init__.py` |

Los 13 módulos: `auth` (usuarios), `perfil`, `dispositivo`, `academico`, `cursos`,
`material`, `clase`, `tarea`, `horario`, `asistencia`, `nota`, `conducta`, `cita`.

## 2. El patrón (memorízalo)

**Route** — corta: protege, saca datos, llama al service, responde.

```python
@bp.post("/<int:id_carga>")                       # método + URL
@jwt_required("DOCENTE")                          # quién puede (401 sin token, 403 otro rol)
def publicar(id_carga):
    return jsonify(material_service.publicar(usuario_actual(), id_carga, json_requerido())), 201
```

**Service** — valida, aplica reglas, maneja la transacción.

```python
def publicar(usuario, id_carga, datos):
    carga = cursos_service.buscar_carga(id_carga)               # 404 si no existe
    cursos_service.exigir_docente_del_curso(usuario, carga)     # 403 si no es su curso
    titulo = texto(datos, "titulo", minimo=3, maximo=150)       # 400 si es inválido

    db = get_db()
    try:
        id_material = material_repository.crear(id_carga, titulo, ...)
        db.commit()                                             # guardar
    except Exception:
        db.rollback()                                           # deshacer todo
        raise
    return {"message": "Material publicado", ...}
```

**Repository** — solo SQL, con `%s` para los valores.

```python
def crear(id_carga, titulo, bimestre, descripcion, archivo_url):
    return insertar("""
        INSERT INTO material_clase (id_carga_academica, titulo, bimestre, descripcion, archivo_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_carga, titulo, bimestre, descripcion, archivo_url))
```

Funciones de `app/database.py` para el repository:

| Función | Para | Devuelve |
|---|---|---|
| `consultar_uno(sql, params)` | SELECT de una fila | dict o `None` |
| `consultar_todos(sql, params)` | SELECT de varias filas | lista de dicts |
| `insertar(sql, params)` | INSERT | id de la fila nueva |
| `ejecutar(sql, params)` | UPDATE / DELETE | cuántas filas cumplieron el WHERE |

Validadores de `app/utils.py` (todos lanzan 400 con un mensaje claro):
`texto`, `entero`, `numero`, `fecha`, `fecha_hora`, `enlace`, `fecha_de_query`.

Errores: `raise ApiError(código, "mensaje")` → responde `{"detail": "mensaje"}`.
400 datos mal · 401 sin sesión · 403 sin permiso · 404 no existe · 409 conflicto.

---

## 3. Recetas

### Receta A — Endpoint nuevo de consulta (GET con JOIN)

> *"El auxiliar debe ver los reportes de conducta registrados en una fecha."*
> `GET /conducta/reportes?fecha=2026-10-02` (AUXILIAR, PSICOLOGO, ADMIN)

**1. Repository** — `app/repositories/conducta_repository.py`

```python
def reportes_del_dia(dia) -> list:
    """Reportes registrados en una fecha, con el alumno y la falta."""
    return consultar_todos("""
        SELECT r.id_reporte, CONCAT(a.nombres, ' ', a.apellidos) AS alumno,
               nc.nombre AS falta, nc.puntos, r.descripcion_suceso, r.estado, r.fecha_reporte
        FROM reporte_conducta r
        JOIN alumno a ON a.id_alumno = r.id_alumno
        JOIN nivel_conducta nc ON nc.id_nivel_conducta = r.id_nivel_conducta
        WHERE DATE(r.fecha_reporte) = %s
        ORDER BY r.fecha_reporte
    """, (dia,))
```

**2. Service** — `app/services/conducta_service.py`

```python
def reportes_del_dia(dia=None) -> dict:
    dia = dia or date.today()            # si no viene ?fecha, hoy
    return {"fecha": dia, "reportes": conducta_repository.reportes_del_dia(dia)}
```

**3. Route** — `app/routes/conducta_routes.py` (agrega `fecha_de_query` al import de `app.utils`)

```python
@bp.get("/reportes")
@jwt_required("AUXILIAR", "PSICOLOGO", "ADMIN")
def reportes_del_dia():
    return jsonify(conducta_service.reportes_del_dia(fecha_de_query()))
```

**4. Probar** en Postman con el token del auxiliar: `GET {{base_url}}/conducta/reportes?fecha=2026-10-02`.

---

### Receta B — Nueva validación en el Service

> *"El teléfono debe tener exactamente 9 dígitos y empezar con 9."*

En `app/services/perfil_service.py`, dentro de `actualizar_contacto`, después de leer `telefono`:

```python
    if telefono and (len(telefono) != 9 or not telefono.isdigit() or not telefono.startswith("9")):
        raise ApiError(400, "El teléfono debe tener 9 dígitos y empezar con 9")
```

Probar: `PATCH /perfil/contacto/ALU-33333333` con `{"telefono": "12345"}` → 400.

---

### Receta C — Endpoint con regla de negocio y transacción (PATCH)

> *"El alumno puede cancelar su propia cita mientras esté PENDIENTE."*
> `PATCH /citas/<id_cita>/cancelar-mia` (ALUMNO) con `{"motivo": "..."}`

**1. Repository**: ya existe `cita_repository.cancelar(id_cita, motivo)`. No hay que tocarlo.

**2. Service** — `app/services/cita_service.py`

```python
def cancelar_mia(usuario: dict, id_cita: int, datos: dict) -> dict:
    motivo = texto(datos, "motivo", minimo=5, maximo=300)
    cita = _buscar(id_cita)                                       # 404
    alumno = perfil_repository.alumno_por_usuario(usuario["id"])
    if alumno is None or cita["id_alumno"] != alumno["id_alumno"]:
        raise ApiError(403, "Solo puedes cancelar tus propias citas")
    _exigir_estado(cita, "PENDIENTE")                             # 409 si ya fue programada

    db = get_db()
    try:
        cita_repository.cancelar(id_cita, motivo)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Cita cancelada"}
```

**3. Route** — `app/routes/cita_routes.py`

```python
@bp.patch("/<int:id_cita>/cancelar-mia")
@jwt_required("ALUMNO")
def cancelar_mia(id_cita):
    return jsonify(cita_service.cancelar_mia(usuario_actual(), id_cita, json_requerido()))
```

**4. Probar**: Mateo tiene una cita PENDIENTE (id 2). Con su token → 200. Repetir → 409.
Con el token de Lucía → 403.

---

### Receta D — Agregar una columna (cambio en las 4 capas)

> *"Guardar qué usuario registró la asistencia."*

**1. Base de datos** — en phpMyAdmin (pestaña SQL) y también en `database/schema.sql`:

```sql
ALTER TABLE asistencia ADD COLUMN registrado_por INT NULL,
  ADD CONSTRAINT asistencia_registrado_fk FOREIGN KEY (registrado_por) REFERENCES usuario (id_usuario);
```

**2. Repository** — `asistencia_repository.registrar`: agrega el parámetro y la columna.

```python
def registrar(id_matricula, fecha, estado, observacion, registrado_por) -> int:
    return insertar("""
        INSERT INTO asistencia (id_matricula, fecha, estado, observacion, registrado_por)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_matricula, fecha, estado, observacion, registrado_por))
```

**3. Service** — `asistencia_service.registrar_lote`: recibe `usuario` y lo pasa.

```python
def registrar_lote(usuario: dict, datos: dict) -> dict:
    ...
            asistencia_repository.registrar(id_matricula, dia, estado, observacion, usuario["id"])
```

**4. Route** — `asistencia_routes.registrar_lote`: envía el usuario del token.

```python
    return jsonify(asistencia_service.registrar_lote(usuario_actual(), json_requerido())), 201
```

Regla de oro: si cambias los parámetros de una función, **busca todos los lugares que
la llaman** (en VS Code: clic derecho → "Find All References" o Ctrl+Shift+F).

---

### Receta E — Filtro opcional en un GET

> *"En mis citas, poder filtrar por estado: `/citas/mis-citas?estado=ATENDIDA`."*

**Repository** (`cita_repository.de_alumno`): agrega el filtro solo si viene.

```python
def de_alumno(id_alumno: int, estado=None) -> list:
    sql = """
        SELECT id_cita, motivo, disponibilidad, fecha_solicitud, fecha_cita, estado, motivo_cancelacion
        FROM cita_psicologia
        WHERE id_alumno = %s
    """
    params = [id_alumno]
    if estado is not None:
        sql += " AND estado = %s"
        params.append(estado)
    sql += " ORDER BY fecha_solicitud DESC"
    return consultar_todos(sql, tuple(params))
```

**Service** (`cita_service.mis_citas`): recibe `estado` y valida.

```python
def mis_citas(usuario: dict, estado=None) -> list:
    if estado is not None and estado not in ("PENDIENTE", "PROGRAMADA", "ATENDIDA", "CANCELADA"):
        raise ApiError(400, "Estado no válido")
    ...
    return cita_repository.de_alumno(alumno["id_alumno"], estado)
```

**Route**: `estado = request.args.get("estado")` y se pasa al service
(agrega `request` al import de `flask`).

---

### Receta F — Cambios de una línea

| Me piden… | Cambio |
|---|---|
| que el docente también registre asistencia | `asistencia_routes.py`: `@jwt_required("AUXILIAR", "DOCENTE")` |
| que la nota aprobatoria sea 13 | `nota_service.py`: `NOTA_APROBATORIA = 13` |
| que no se acepten tareas fuera de plazo (409) | `tarea_service.py`: `ACEPTAR_FUERA_DE_PLAZO = False` |
| que el docente pueda volver a calificar | `tarea_service.calificar`: quitar el `if entrega["calificacion"] is not None` |
| que la observación al calificar sea obligatoria | `tarea_service.calificar`: `texto(datos, "observacion", minimo=3, maximo=1000)` |
| que el token dure 2 horas | `.env`: `ACCESS_TOKEN_EXPIRE_MINUTES=120` |
| que el título del material tenga mínimo 5 letras | `material_service._validar`: `minimo=5` |
| que un reporte de conducta pueda tener fecha futura | quitar el `if dia > date.today()` en `conducta_service` |
| que un registro duplicado responda 409 | `raise ApiError(409, "...")` en el service |

---

## 4. Transacciones: qué decir

- La conexión tiene `autocommit=False`: **nada se guarda hasta `db.commit()`**.
- Si ocurre un error en medio, `db.rollback()` **deshace todos los cambios** de esa operación.
- Ejemplos con varios cambios relacionados:
  - `POST /asistencia/lote`: borra la asistencia previa del día + inserta un registro por alumno.
  - `POST /notas/<id_carga>`: una nota por alumno.
  - `POST /notas/<id_carga>/cerrar-bimestre`: un promedio por alumno en la libreta + el registro del cierre.
  - `PATCH /perfil/contacto/...` (alumno sin familiar): crea el familiar + lo enlaza.
- Para comprobarlo: en phpMyAdmin, antes y después de la petición, mira la tabla.

## 5. Si algo falla

| Síntoma | Causa probable |
|---|---|
| `503 No se pudo conectar con la base de datos` | MySQL de XAMPP apagado, o puerto/clave mal en `.env` |
| `401 Token expirado` | pasaron 60 min: vuelve a hacer login |
| `401 No se encontró el token` | falta la pestaña Authorization → Bearer en Postman |
| `500 Error interno` | un bug: mira la consola donde corre `python run.py` (sale el error exacto) |
| `KeyError: 'nombre'` en la consola | la columna se llama distinto en el SELECT (revisa los alias `AS`) |
| `not enough arguments for format string` | hay más `%s` en el SQL que valores en la tupla |
| `Unknown column` | la columna no existe: revisa `database/schema.sql` o phpMyAdmin |
| el cambio no se guardó | falta `db.commit()` en el service |
| `404` en una ruta nueva | no se registró el blueprint en `app/__init__.py`, o la URL no coincide |
| `405 Method Not Allowed` | método equivocado (GET en vez de POST, etc.) |

Para dejar la demo como al principio: `flask --app run reiniciar-demo`.

## 6. Preguntas de sustentación

- **¿Por qué Route, Service y Repository separados?** Cada capa tiene un solo trabajo:
  la route habla HTTP, el service decide (reglas y transacción), el repository habla SQL.
  Se puede cambiar una sin tocar las otras, y una misma regla se reutiliza.
- **¿Por qué `%s` y no armar el SQL con f-strings?** Para evitar la inyección SQL:
  PyMySQL escapa los valores. Solo se usan f-strings para nombres de tablas/columnas
  que vienen de una lista fija del código (ej. `TABLA_POR_ROL`), nunca del usuario.
- **¿Qué pasa si falla una inserción a mitad del lote?** El `except` hace `rollback()`
  y no queda ningún registro a medias; la API responde el error.
- **¿Cómo funciona el JWT?** En el login se firma un token con `SECRET_KEY` que lleva
  id, rol y vencimiento. `@jwt_required` verifica la firma y el vencimiento en cada
  petición. Si alguien altera el token, la firma no coincide → 401.
- **¿Diferencia entre 401 y 403?** 401: no sé quién eres. 403: sé quién eres, pero no puedes.
- **¿Dónde se valida?** En el service, con los validadores de `utils.py`.
- **¿Cómo se guarda la contraseña?** Hash bcrypt; nunca la contraseña.
- **¿Qué es el primer ingreso?** `usuario.debe_cambiar_password = 1`. El login lo
  devuelve y la app obliga a cambiar la clave; `change-password` lo pone en 0.
- **¿Cómo se calcula la nota de conducta?** 20 − SUM(puntos) de los reportes vigentes
  del bimestre, con un `LEFT JOIN` + `GROUP BY` por bimestre (`conducta_repository`).
- **¿Cómo sabe el alumno el estado de su tarea?** `LEFT JOIN entrega_tarea ... AND
  e.id_alumno = %s`: si no hay entrega, sale NULL → PENDIENTE (o VENCIDA si pasó la fecha);
  con nota → CALIFICADA; sin nota → ENTREGADA. Lo calcula `tarea_service._estado_entrega`.
- **¿Cómo se cierra un bimestre?** Se calcula el `AVG` de las evaluaciones de cada
  alumno, se guarda en `resumen_nota` (libreta) y se registra en `cierre_bimestre`,
  todo en una transacción. Después ya no se aceptan notas de ese bimestre (409).

## 7. Plan para los 20 minutos

1. **(2 min)** Lee el requerimiento y decide: ¿qué URL?, ¿qué rol?, ¿qué tabla?, ¿qué regla?
2. **(3 min)** Abre los 3 archivos del módulo y **copia una función parecida** que ya exista.
3. **(10 min)** Repository (SQL) → Service (validación + reglas + commit/rollback) → Route.
4. **(3 min)** Prueba en Postman el caso correcto y un caso de error. Mira la tabla en phpMyAdmin.
5. **(2 min)** Repasa qué vas a explicar: el recorrido Route → Service → Repository → BD.
