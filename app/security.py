"""Contraseñas con bcrypt.

Nunca se guarda la contraseña tal cual: se guarda su "hash", un texto del que no
se puede recuperar la contraseña original. Para comprobar un login se calcula el
hash de lo que escribió el usuario y se compara con el guardado.
"""
import bcrypt

from app import config


def get_password_hash(password: str) -> str:
    """Convierte una contraseña en su hash para guardarla en la base."""
    # La "sal" es un valor aleatorio: dos usuarios con la misma clave tienen hashes distintos.
    sal = bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), sal).decode("utf-8")


def verify_password(password: str, hash_guardado: str) -> bool:
    """True si la contraseña escrita corresponde al hash guardado en la base."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):   # hash vacío o con formato inválido
        return False
