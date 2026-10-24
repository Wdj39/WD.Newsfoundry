"""Logique métier des discussions : autorisations, historique, appel de l'agent."""

import logging

from fastapi import HTTPException, status
from pydantic_ai import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.exceptions import (
    FallbackExceptionGroup,
    ModelAPIError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)
from pydantic_ai.models import Model
from sqlmodel import Session

from agents.chat_agent import ChatDeps, chat_agent
from agents.prompts import build_chat_system_prompt
from models import Chat, User, utc_now
from schemas import MessageView
from services.news_api import NewsAPIError, NewsClient, get_top_news_cached

logger = logging.getLogger(__name__)


def get_owned_chat(session: Session, chat_id: int, user: User) -> Chat:
    """Retourne la discussion si elle appartient à l'utilisateur, sinon lève une 404.

    On renvoie 404 (et non 403) quand la discussion appartient à un autre
    utilisateur : les identifiants étant des entiers successifs, un 403 révélerait
    qu'une discussion existe avec cet identifiant.
    """
    chat = session.get(Chat, chat_id)
    if chat is None or chat.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion introuvable.",
        )
    return chat


async def build_system_prompt_with_news(news_client: NewsClient) -> str:
    """Prompt système d'une nouvelle discussion, enrichi des actualités du jour.

    Si World News API est indisponible (quota épuisé, panne, clé absente…), la
    discussion est quand même créée : le prompt indique alors au modèle qu'il ne
    dispose pas de l'actualité, pour qu'il le signale au lieu d'inventer.
    """
    try:
        news = await get_top_news_cached(news_client)
    except NewsAPIError as exc:
        logger.warning("Actualités du jour indisponibles : %s", exc)
        news = None
    return build_chat_system_prompt(news)


def load_history(chat: Chat) -> list[ModelMessage]:
    """Désérialise l'historique JSON stocké en base en messages PydanticAI."""
    return ModelMessagesTypeAdapter.validate_python(chat.messages)


def to_message_views(history: list[ModelMessage]) -> list[MessageView]:
    """Convertit l'historique PydanticAI en messages simples à afficher.

    L'historique brut contient aussi les appels d'outils et leurs résultats
    (étapes suivantes) : on ne garde que ce que l'utilisateur doit voir,
    c'est-à-dire ses messages et les réponses textuelles de l'agent.
    """
    views: list[MessageView] = []
    for message in history:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    views.append(
                        MessageView(role="user", content=part.content, created_at=part.timestamp)
                    )
        elif isinstance(message, ModelResponse):
            text = "".join(part.content for part in message.parts if isinstance(part, TextPart))
            if text.strip():
                views.append(
                    MessageView(role="assistant", content=text, created_at=message.timestamp)
                )
    return views


async def send_message(session: Session, chat: Chat, content: str, llm: Model) -> MessageView:
    """Envoie un message à l'agent, sauvegarde l'historique et retourne la réponse."""
    history = load_history(chat)

    try:
        result = await chat_agent.run(
            content,
            message_history=history,
            deps=ChatDeps(system_prompt=chat.system_prompt),
            model=llm,
        )
    except (ModelAPIError, FallbackExceptionGroup):
        # Erreur côté fournisseur (quota, panne, surcharge) sur tous les modèles
        logger.exception("Échec de l'appel au LLM")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service d'IA est momentanément indisponible. Réessayez dans quelques instants.",
        )
    except (UnexpectedModelBehavior, UsageLimitExceeded):
        # Le modèle a répondu, mais sa réponse est inexploitable
        logger.exception("Réponse du LLM inexploitable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="L'IA n'a pas pu produire de réponse. Essayez de reformuler votre message.",
        )

    # On ne sauvegarde qu'en cas de succès : un échec ne laisse pas de message
    # utilisateur orphelin (sans réponse) dans l'historique.
    # Une nouvelle liste est assignée pour que SQLAlchemy détecte la modification du JSON.
    chat.messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
    chat.updated_at = utc_now()
    session.add(chat)
    session.commit()

    return MessageView(
        role="assistant",
        content=result.output,
        created_at=result.response.timestamp,
    )
