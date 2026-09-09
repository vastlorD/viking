"""Hash de senha com salt individual, sem senhas padrão."""

import hashlib
import hmac
import secrets

ITERATIONS = 600_000


def hash_password(password):
    if not 12 <= len(password) <= 128:
        raise ValueError("A senha deve ter de 12 a 128 caracteres.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    if not 1 <= len(password) <= 128:
        return False
    try:
        algorithm, rounds, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(rounds) <= 2_000_000:
            return False
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(computed, bytes.fromhex(digest))
    except (ValueError, TypeError, AttributeError):
        return False
