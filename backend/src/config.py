"""Configuration de l'application, lue depuis les variables d'environnement.

Centraliser la lecture des variables ici évite d'appeler `os.getenv`
partout dans le code et permet d'échouer tôt si une variable obligatoire manque.
"""

import os


def _require(name: str) -> str:
    """Retourne la valeur d'une variable d'environnement obligatoire."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"La variable d'environnement {name} est manquante (voir .env.example)."
        )
    return value


DATABASE_URL = _require("DATABASE_URL")

# --- Authentification JWT ---
JWT_SECRET = _require("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 h

# --- LLM ---
# Facultatives au démarrage : les tests n'appellent jamais de vrai modèle.
# Si aucune clé n'est fournie, l'API répond une erreur claire au moment du chat.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Noms de modèles configurables : les fournisseurs retirent régulièrement d'anciens modèles
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# --- CORS ---
# Origines autorisées à appeler l'API, séparées par des virgules.
# En local : le serveur Next.js ; en production : l'URL Vercel.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
