# AmancioApp Backend — aplicación móvil

API construida con FastAPI para la aplicación móvil del Campus AV. El alcance
funcional está definido en [alcance_del_proyecto.md](./alcance_del_proyecto.md).

## Funcionalidades móviles

- Inicio de sesión, control por rol y cambio de contraseña en el primer ingreso.
- Consulta de perfil, matrícula del año activo (sin información económica),
  cursos, horarios, notas, libretas y asistencia.
- Registro y consulta de reportes de conducta, catálogo de faltas y notas de
  conducta por bimestre.
- Solicitud y seguimiento de citas de psicología.
- Materiales, clases virtuales, tareas, entregas y mensajería interna.
- Recursos de notificación y archivos necesarios para las funciones del campus.

La API publica únicamente las rutas móviles seleccionadas en `main.py`. No
publica las operaciones financieras, administrativas ni de contenido web
excluidas del alcance. Los modelos y servicios compartidos con las funciones
móviles se conservan; no se eliminan tablas ni datos de la base de datos.
Los archivos públicos se limitan a `/media/materiales_clase`,
`/media/recursos_tareas` y `/media/entregas_tareas`.

## Ejecución local

1. Crear y activar un entorno virtual de Python 3.12.
2. Instalar dependencias con `pip install -r requirements.txt`.
3. Configurar las variables necesarias tomando `.env.example` como referencia.
4. Iniciar el servidor:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

El servidor necesita conexión con la base de datos configurada en el entorno.
La documentación interactiva y el esquema OpenAPI dependen de la configuración
del entorno.
