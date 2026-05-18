import hashlib
import hmac


def hash_password(raw_password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    )
    return derived.hex()


def verify_password(raw_password: str, hashed_password: str, salt: str) -> bool:
    current_hash = hash_password(raw_password, salt)
    return hmac.compare_digest(current_hash, hashed_password)
