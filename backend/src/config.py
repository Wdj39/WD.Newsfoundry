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

# --- Actualités (https://worldnewsapi.com) ---
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY", "")
NEWS_COUNTRY = os.getenv("NEWS_COUNTRY", "fr")  # pays des sources (code ISO)
NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "fr")  # langue des articles
# Nombre maximal de sujets injectés dans le prompt système (garde le prompt court)
NEWS_MAX_TOP_STORIES = int(os.getenv("NEWS_MAX_TOP_STORIES", "15"))
# Nombre d'articles renvoyés par une recherche de l'agent (tool search_news)
NEWS_SEARCH_MAX_RESULTS = int(os.getenv("NEWS_SEARCH_MAX_RESULTS", "5"))
# Nombre maximal de recherches que l'agent peut lancer pour répondre à un message
NEWS_MAX_SEARCHES_PER_MESSAGE = int(os.getenv("NEWS_MAX_SEARCHES_PER_MESSAGE", "3"))
# Durée de mise en cache des gros titres : évite de consommer le quota
# de l'API à chaque nouvelle discussion
NEWS_CACHE_SECONDS = int(os.getenv("NEWS_CACHE_SECONDS", "3600"))

# --- CORS ---
# Origines autorisées à appeler l'API, séparées par des virgules.
# En local : le serveur Next.js ; en production : l'URL Vercel.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
