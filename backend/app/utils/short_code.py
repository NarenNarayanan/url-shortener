"""
Short code generation. Uses `secrets` (not `random`) because these codes are
guessable-URL security surface — a predictable code lets someone enumerate
other users' links.
"""
import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
