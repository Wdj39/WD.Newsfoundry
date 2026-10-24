"""Génération des revues de presse à partir d'une discussion."""

import logging
import time

from fastapi import HTTPException, status
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic_ai import ModelRequest, ModelResponse, TextPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models import Model
from sqlmodel import Session

from agents.prompts import build_review_prompt
from agents.review_agent import review_agent
from models import Chat, utc_now
from schemas import ReviewView
from services.chat_service import load_history
from services.llm_errors import handle_llm_errors
from services.rag import format_retrieved_articles, retrieve_relevant_articles

logger = logging.getLogger(__name__)

NEWS_SECTION_MARKER = "## Actualités du jour"


def _format_tool_result(content: object) -> str:
    """Met en forme les articles renvoyés par le tool search_news."""
    if not isinstance(content, list):
        return f"(Recherche) {content}"
    lines = ["Articles trouvés par recherche :"]
    for article in content:
        if isinstance(article, dict):
            lines.append(
                f"- {article.get('titre', '')} — {article.get('resume', '')} "
                f"({article.get('date', '')} · {article.get('url', '')})"
            )
    return "\n".join(lines)


def build_conversation_transcript(chat: Chat, include_articles: bool = True) -> str:
    """Transforme la discussion en un texte lisible par l'agent de revue de presse.

    Plutôt que de transmettre l'historique PydanticAI brut (qui contient des appels
    à un outil que cet agent ne possède pas), on construit une transcription qui
    contient tout le contexte utile :
    - les gros titres du jour injectés dans le prompt de la discussion ;
    - les messages échangés ;
    - les articles chargés par l'agent avec search_news.

    Avec le RAG, `include_articles=False` : les articles sont alors fournis à
    part, sous forme d'extraits pertinents, et la transcription ne garde que
    l'échange entre le journaliste et l'assistant.
    """
    parts: list[str] = []

    if include_articles and NEWS_SECTION_MARKER in chat.system_prompt:
        news = chat.system_prompt.split(NEWS_SECTION_MARKER, 1)[1].strip()
        parts.append(f"[Gros titres du jour fournis à l'assistant]\n{news}")

    for message in load_history(chat):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    parts.append(f"[Journaliste]\n{part.content}")
                elif include_articles and isinstance(part, ToolReturnPart):
                    parts.append(f"[Outil de recherche]\n{_format_tool_result(part.content)}")
        elif isinstance(message, ModelResponse):
            text = "".join(p.content for p in message.parts if isinstance(p, TextPart)).strip()
            if text:
                parts.append(f"[Assistant]\n{text}")

    return "\n\n".join(parts)


def to_review_view(chat: Chat) -> ReviewView:
    return ReviewView(
        chat_id=chat.id,
        topic=chat.review_topic or "",
        title=chat.review_title or "",
        summary=chat.review_summary or "",
        articles=chat.review_articles or [],
        generated_at=chat.review_generated_at,
    )


async def build_review_input(chat: Chat, topic: str, embed_model: BaseEmbedding | None) -> str:
    """Prépare le message de l'agent de revue de presse, avec RAG si possible.

    Repli sans RAG (transcription complète, avec les résumés des articles) si
    aucun modèle d'embedding n'est configuré, si aucun article n'a été chargé ou
    si le calcul des embeddings échoue : la revue reste générée.
    """
    if embed_model is not None and chat.loaded_articles:
        start = time.perf_counter()
        try:
            retrieved = await retrieve_relevant_articles(chat.loaded_articles, topic, embed_model)
        except Exception:  # erreurs réseau, quota, modèle indisponible…
            logger.exception("RAG indisponible : génération à partir de la discussion seule")
        else:
            logger.info(
                "RAG : %d extraits de %d articles retenus parmi %d articles chargés (%.1f s)",
                sum(len(a.excerpts) for a in retrieved),
                len(retrieved),
                len(chat.loaded_articles),
                time.perf_counter() - start,
            )
            if retrieved:
                return build_review_prompt(
                    topic,
                    build_conversation_transcript(chat, include_articles=False),
                    format_retrieved_articles(retrieved),
                )

    return build_review_prompt(topic, build_conversation_transcript(chat))


async def generate_review(
    session: Session,
    chat: Chat,
    topic: str,
    llm: Model,
    embed_model: BaseEmbedding | None = None,
) -> ReviewView:
    """Génère la revue de presse d'une discussion et l'enregistre en base."""
    if not chat.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La discussion est vide : échangez d'abord avec l'assistant.",
        )

    prompt = await build_review_input(chat, topic, embed_model)
    with handle_llm_errors("Réessayez dans quelques instants."):
        result = await review_agent.run(prompt, model=llm)

    review = result.output
    chat.review_topic = topic
    chat.review_title = review.title
    chat.review_summary = review.summary
    chat.review_articles = [article.model_dump() for article in review.articles]
    chat.review_generated_at = utc_now()
    session.add(chat)
    session.commit()
    session.refresh(chat)

    return to_review_view(chat)
