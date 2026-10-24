"""Hachage des mots de passe et gestion des tokens JWT."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, JWT_SECRET


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt.

    `bcrypt.hashpw` retourne des bytes : on les décode en str pour que la
    colonne VARCHAR de PostgreSQL stocke bien "$2b$12$..." et non une
    représentation hexadécimale ("\\x2432...") qui rendrait la vérification impossible.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Hash mal formé en base : on refuse la connexion plutôt que de planter.
        return False


def create_access_token(user_id: int) -> str:
    """Crée un JWT signé contenant l'identifiant de l'utilisateur."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # "subject" : à qui appartient le token
        "iat": now,  # date d'émission
        "exp": now + timedelta(minutes=JWT_EXPIRATION_MINUTES),  # date d'expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Décode un JWT et retourne l'identifiant de l'utilisateur.

    Lève `jwt.InvalidTokenError` si le token est invalide, falsifié ou expiré.
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])
