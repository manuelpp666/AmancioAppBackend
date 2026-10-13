"""Routes: los endpoints de la API. Cada archivo es un módulo (blueprint) con su
prefijo de URL.

Una route solo: (1) protege el endpoint con @jwt_required, (2) saca los datos
de la petición (JSON, URL, usuario del token), (3) llama al service y
(4) devuelve la respuesta en JSON con su código HTTP.
"""
