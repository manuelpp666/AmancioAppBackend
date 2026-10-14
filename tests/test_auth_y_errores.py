"""Pruebas automáticas que NO necesitan base de datos: JWT, errores y utilidades.

Ejecutar:  python -m unittest discover -s tests -v

Cada prueba arma una mini-app de Flask con rutas de ejemplo protegidas por
`@jwt_required`, les hace peticiones y revisa el código de respuesta.
"""
import datetime as dt
import os
import unittest
from decimal import Decimal

# Una SECRET_KEY de prueba, antes de importar la app (config la lee al cargarse).
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("ENTORNO", "desarrollo")

import jwt  # noqa: E402
from flask import Flask, jsonify  # noqa: E402

from app import config  # noqa: E402
from app.auth import crear_token, exigir_dueno_o_roles, jwt_required, usuario_actual  # noqa: E402
from app.errors import ApiError, registrar_errores  # noqa: E402
from app.utils import ProveedorJSON, enlace, entero, extraer_dni, fecha, fecha_hora, hora_texto, lista, numero, texto  # noqa: E402


def construir_app():
    """Mini-app con rutas de ejemplo para probar la seguridad y los errores."""
    app = Flask(__name__)
    app.json = ProveedorJSON(app)
    registrar_errores(app)

    @app.get("/privada")                 # cualquier usuario con token
    @jwt_required()
    def privada():
        return jsonify(usuario_actual())

    @app.get("/solo-docente")            # solo el rol DOCENTE
    @jwt_required("DOCENTE")
    def solo_docente():
        return jsonify({"ok": True})

    @app.get("/dueno/<int:uid>")         # solo el dueño (mismo id) o un ADMIN
    @jwt_required()
    def dueno(uid):
        exigir_dueno_o_roles(usuario_actual(), uid, "ADMIN")
        return jsonify({"ok": True})

    @app.get("/boom")                    # simula un error inesperado (bug)
    def boom():
        raise RuntimeError("secreto interno")

    @app.get("/fechas")                  # para revisar cómo salen fechas y decimales
    def fechas():
        return jsonify({"f": dt.date(2026, 3, 9), "dt": dt.datetime(2026, 3, 9, 7, 30), "n": Decimal("14.50")})

    return app


def usuario(rol="ALUMNO", id_=7, nombre="ALU-12345678"):
    """Usuario falso (sin base de datos) para crear tokens: igual a una fila de `usuario`."""
    return {"username": nombre, "id_usuario": id_, "rol": rol}


def cab(token):
    """Cabecera Authorization con el token."""
    return {"Authorization": f"Bearer {token}"}


class PruebasJWT(unittest.TestCase):
    """El token: cuándo se acepta y cuándo se rechaza."""

    def setUp(self):
        self.c = construir_app().test_client()

    def test_sin_token_da_401(self):
        r = self.c.get("/privada")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.headers["WWW-Authenticate"], "Bearer")
        self.assertIn("detail", r.get_json())

    def test_token_valido_pasa_y_trae_id_rol_y_sub(self):
        r = self.c.get("/privada", headers=cab(crear_token(usuario())))
        self.assertEqual(r.status_code, 200)
        p = r.get_json()
        self.assertEqual((p["sub"], p["id"], p["rol"]), ("ALU-12345678", 7, "ALUMNO"))

    def test_token_expirado_da_401(self):
        ahora = dt.datetime.now(dt.timezone.utc)
        t = jwt.encode({"sub": "a", "id": 1, "rol": "ALUMNO", "exp": ahora - dt.timedelta(seconds=5)},
                       config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        r = self.c.get("/privada", headers=cab(t))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()["detail"], "Token expirado")

    def test_firma_incorrecta_da_401(self):
        # Token firmado con otra clave: alguien intentando falsificarlo.
        t = jwt.encode({"sub": "a", "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)},
                       "otra-clave-distinta-de-32-caracteres!!", algorithm="HS256")
        r = self.c.get("/privada", headers=cab(t))
        self.assertEqual((r.status_code, r.get_json()["detail"]), (401, "Token inválido"))

    def test_token_sin_firma_alg_none_es_rechazado(self):
        # Ataque clásico: un token "sin firma" que dice ser ADMIN.
        t = jwt.encode({"sub": "a", "rol": "ADMIN", "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)},
                       None, algorithm="none")
        self.assertEqual(self.c.get("/privada", headers=cab(t)).status_code, 401)

    def test_token_sin_exp_es_rechazado(self):
        # Un token sin fecha de vencimiento no se acepta.
        t = jwt.encode({"sub": "a"}, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        self.assertEqual(self.c.get("/privada", headers=cab(t)).status_code, 401)

    def test_cabecera_mal_formada_da_401(self):
        r = self.c.get("/privada", headers={"Authorization": "Token abc"})
        self.assertEqual(r.status_code, 401)

    def test_rol_no_permitido_da_403_y_permitido_200(self):
        self.assertEqual(self.c.get("/solo-docente", headers=cab(crear_token(usuario("ALUMNO")))).status_code, 403)
        self.assertEqual(self.c.get("/solo-docente", headers=cab(crear_token(usuario("DOCENTE")))).status_code, 200)

    def test_dueno_o_admin(self):
        mio = cab(crear_token(usuario("ALUMNO", id_=7)))
        self.assertEqual(self.c.get("/dueno/7", headers=mio).status_code, 200)   # su propio dato
        self.assertEqual(self.c.get("/dueno/8", headers=mio).status_code, 403)   # dato de otro
        admin = cab(crear_token(usuario("ADMIN", id_=1)))
        self.assertEqual(self.c.get("/dueno/8", headers=admin).status_code, 200)  # el admin sí puede


class PruebasErrores(unittest.TestCase):
    """Todos los errores salen en JSON y sin filtrar información interna."""

    def setUp(self):
        self.c = construir_app().test_client()

    def test_404_y_405_salen_en_json(self):
        r = self.c.get("/no-existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("detail", r.get_json())
        self.assertEqual(self.c.post("/privada").status_code, 405)   # método no permitido

    def test_500_no_filtra_el_mensaje_interno(self):
        r = self.c.get("/boom")
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json()["detail"], "Error interno del servidor")
        self.assertNotIn("secreto", r.get_data(as_text=True))

    def test_fechas_iso_y_decimal_numerico(self):
        j = self.c.get("/fechas").get_json()
        self.assertEqual(j, {"f": "2026-03-09", "dt": "2026-03-09T07:30:00", "n": 14.5})


class PruebasUtilidades(unittest.TestCase):
    """Funciones de ayuda de app/utils.py."""

    def test_extraer_dni(self):
        self.assertEqual(extraer_dni("ALU-12345678"), "12345678")
        self.assertEqual(extraer_dni("DOC-87654321"), "87654321")
        self.assertEqual(extraer_dni("12345678"), "12345678")   # sin prefijo
        self.assertEqual(extraer_dni("XYZ-1"), "XYZ-1")         # prefijo desconocido
        self.assertEqual(extraer_dni(""), "")

    def test_texto_valida_largo_y_tipo(self):
        self.assertEqual(texto({"a": "  hola "}, "a"), "hola")   # quita espacios
        with self.assertRaises(ApiError) as e:
            texto({}, "a")                                       # falta y es requerido
        self.assertEqual(e.exception.status, 400)
        with self.assertRaises(ApiError):
            texto({"a": "ab"}, "a", minimo=3)                    # muy corto
        with self.assertRaises(ApiError):
            texto({"a": "x" * 11}, "a", maximo=10)               # muy largo
        with self.assertRaises(ApiError):
            texto({"a": 5}, "a")                                 # no es texto
        self.assertIsNone(texto({}, "a", requerido=False))       # opcional que falta
        self.assertEqual(texto({"a": ""}, "a", minimo=0, requerido=False), "")

    def test_entero_valida_tipo_y_rango(self):
        self.assertEqual(entero({"b": 2}, "b", minimo=1, maximo=4), 2)
        for malo in ({}, {"b": 5}, {"b": 0}, {"b": "2"}, {"b": 2.5}, {"b": True}):
            with self.assertRaises(ApiError):                    # falta, fuera de rango o no es entero
                entero(malo, "b", minimo=1, maximo=4)

    def test_numero_para_notas(self):
        self.assertEqual(numero({"v": 15}, "v", minimo=0, maximo=20), 15.0)
        self.assertEqual(numero({"v": 14.567}, "v", minimo=0, maximo=20), 14.57)   # 2 decimales
        for malo in ({}, {"v": 21}, {"v": -1}, {"v": "15"}, {"v": True}):
            with self.assertRaises(ApiError):                    # falta, fuera de 0-20 o no es número
                numero(malo, "v", minimo=0, maximo=20)

    def test_fechas_y_horas(self):
        self.assertEqual(fecha({"f": "2026-10-13"}, "f"), dt.date(2026, 10, 13))
        self.assertIsNone(fecha({}, "f", requerido=False))
        self.assertEqual(fecha_hora({"f": "2026-10-20T10:00"}, "f"), dt.datetime(2026, 10, 20, 10, 0))
        for malo in ("13/10/2026", "2026-13-01", "hoy"):
            with self.assertRaises(ApiError):
                fecha({"f": malo}, "f")
        with self.assertRaises(ApiError):
            fecha_hora({"f": "20/10/2026 10:00"}, "f")
        self.assertEqual(hora_texto(dt.timedelta(hours=7, minutes=5)), "07:05")   # TIME de MySQL

    def test_enlace(self):
        self.assertEqual(enlace({"u": "https://a.com/x"}, "u"), "https://a.com/x")
        self.assertIsNone(enlace({}, "u"))                       # opcional
        with self.assertRaises(ApiError):
            enlace({"u": "a.com/x"}, "u")                        # sin http(s)
        with self.assertRaises(ApiError):
            enlace({}, "u", requerido=True)

    def test_lista(self):
        self.assertEqual(lista({"l": [3, 4]}, "l"), [3, 4])
        self.assertEqual(lista({"l": []}, "l", minimo=0), [])    # vacía permitida si minimo=0
        for malo in ({}, {"l": None}, {"l": 3}, {"l": "3,4"}, {"l": {"id": 3}}, {"l": []}):
            with self.assertRaises(ApiError) as e:               # falta, no es lista o está vacía
                lista(malo, "l")
            self.assertEqual(e.exception.status, 400)
        with self.assertRaises(ApiError):
            lista({"l": [1, 2, 3]}, "l", maximo=2)               # demasiados elementos


if __name__ == "__main__":
    unittest.main()
