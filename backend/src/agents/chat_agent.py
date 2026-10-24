"""Agent conversationnel du chat NewsFoundry.

L'agent dispose d'un outil (tool) `search_news` qu'il peut décider d'appeler
lui-même pour charger des articles supplémentaires quand l'utilisateur veut
approfondir un sujet absent des gros titres du jour.
"""

import logging
import os
from dataclasses import dataclass, field

# Masque la bannière d'accueil affichée par PydanticAI au premier lancement d'un agent
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, RunContext  # noqa: E402

from config import NEWS_MAX_SEARCHES_PER_MESSAGE  # noqa: E402
from services.news_api import NewsAPIError, NewsClient  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class ChatDeps:
    """Dépendances injectées à chaque exécution de l'agent."""

    # Prompt système propre à la discussion (stocké en base avec le Chat)
    system_prompt: str
    # Client World News API utilisé par le tool de recherche
    news_client: NewsClient
    # Requêtes déjà lancées pendant ce message (limite le quota consommé)
    searches: list[str] = field(default_factory=list)
    # Articles trouvés pendant ce message, enregistrés ensuite dans le Chat (RAG)
    loaded_articles: list[dict[str, str]] = field(default_factory=list)


# Le modèle n'est pas fixé ici : il est passé à chaque `run` (voir agents/llm.py et
# la dépendance `get_chat_model`), ce qui permet aux tests d'utiliser un TestModel.
chat_agent = Agent(deps_type=ChatDeps, name="newsfoundry_chat")


@chat_agent.instructions
def chat_instructions(ctx: RunContext[ChatDeps]) -> str:
    """Instructions envoyées au modèle à chaque appel.

    Contrairement à un `system_prompt` classique (envoyé une seule fois en début
    d'historique), les instructions sont recalculées à chaque appel à partir du
    prompt enregistré pour cette discussion.
    """
    return ctx.deps.system_prompt


@chat_agent.tool
async def search_news(ctx: RunContext[ChatDeps], query: str) -> list[dict[str, str]] | str:
    """Recherche des articles de presse récents sur un sujet précis.

    À utiliser quand l'utilisateur demande des informations, des détails ou des
    sources sur un sujet absent ou peu détaillé dans les actualités du jour.
    Ne pas utiliser pour une simple conversation ni pour des connaissances générales.

    Args:
        query: 2 à 5 mots-clés en français décrivant le sujet, sans phrase
            (ex. "mobilisation intersyndicale retraites", "prix électricité").
    """
    # Garde-fou : on limite le nombre de recherches par message pour préserver
    # le quota de l'API et éviter qu'un modèle ne boucle sur l'outil.
    if len(ctx.deps.searches) >= NEWS_MAX_SEARCHES_PER_MESSAGE:
        return (
            "Limite de recherches atteinte pour ce message : réponds avec les "
            "articles déjà trouvés."
        )
    ctx.deps.searches.append(query)

    try:
        articles = await ctx.deps.news_client.search_news(query)
    except NewsAPIError as exc:
        # On renvoie l'erreur au modèle sous forme de texte : il peut alors
        # prévenir l'utilisateur au lieu de faire échouer toute la réponse.
        logger.warning("Recherche d'actualités impossible (%r) : %s", query, exc)
        return f"Recherche impossible ({exc}). Préviens l'utilisateur."

    if not articles:
        return f"Aucun article récent trouvé pour « {query} »."

    # Contenu complet conservé pour le RAG de la revue de presse (étape 8)
    ctx.deps.loaded_articles.extend(article.to_dict() for article in articles)

    # Format simple et compact pour le LLM : uniquement les champs utiles
    return [
        {
            "titre": article.title,
            "resume": article.summary,
            "date": article.publish_date,
            "url": article.url,
        }
        for article in articles
    ]
