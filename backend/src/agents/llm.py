"""Construction du modèle de langage utilisé par les agents."""

from functools import lru_cache

from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider

from config import GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL


class LLMNotConfiguredError(RuntimeError):
    """Aucune clé d'API de LLM n'est configurée."""


@lru_cache
def get_llm() -> Model:
    """Retourne le modèle à utiliser : Gemini en principal, Groq en secours.

    `FallbackModel` essaie les modèles dans l'ordre : si Gemini renvoie une erreur
    d'API (quota dépassé, panne, surcharge…), la requête est rejouée sur Groq.
    Le modèle est construit à la première utilisation (et mis en cache) pour que
    l'application et les tests puissent démarrer sans clé d'API.
    """
    models: list[Model] = []
    if GEMINI_API_KEY:
        models.append(GoogleModel(GEMINI_MODEL, provider=GoogleProvider(api_key=GEMINI_API_KEY)))
    if GROQ_API_KEY:
        models.append(GroqModel(GROQ_MODEL, provider=GroqProvider(api_key=GROQ_API_KEY)))

    if not models:
        raise LLMNotConfiguredError("Définissez GEMINI_API_KEY et/ou GROQ_API_KEY.")
    if len(models) == 1:
        return models[0]
    return FallbackModel(*models)
