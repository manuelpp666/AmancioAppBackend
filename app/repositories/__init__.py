"""Repositories: la ÚNICA capa que habla con la base de datos.

Cada función ejecuta una consulta SQL y devuelve el resultado. No valida datos,
no revisa permisos y no hace commit: eso le toca al Service.
"""
