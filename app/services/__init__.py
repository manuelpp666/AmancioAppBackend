"""Services: reglas de negocio, validaciones y transacciones.

Un service recibe los datos ya extraídos de la petición (el JSON, el usuario
del token), los valida, decide qué hacer, llama a los repositories y, cuando
hay cambios en la base, confirma con COMMIT o deshace con ROLLBACK.
"""
