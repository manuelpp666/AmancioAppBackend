"""Contraseñas: hash con bcrypt (mismo formato que la base del campus web)."""
import bcrypt

from app import config


def get_password_hash(password: str) -> str:
    sal = bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), sal).decode("utf-8")


def verify_password(plana: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(plana.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False
