"""Routes des revues de presse. Toutes nécessitent un utilisateur authentifié."""

from fastapi import APIRouter, Depends, HTTPException, status
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic_ai.models import Model
from sqlmodel import Session, col, select

from database import get_session
from dependencies import get_chat_model, get_current_user, get_embedding_model_or_none
from models import Chat, User
from schemas import GenerateReviewRequest, ReviewView
from services.chat_service import get_owned_chat
from services.review_service import generate_review, to_review_view

router = APIRouter(tags=["reviews"])


@router.post("/chats/{chat_id}/review", response_model=ReviewView)
async def create_review(
    chat_id: int,
    body: GenerateReviewRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    llm: Model = Depends(get_chat_model),
    embed_model: BaseEmbedding | None = Depends(get_embedding_model_or_none),
) -> ReviewView:
    """Génère (ou régénère) la revue de presse d'une discussion sur un thème."""
    chat = get_owned_chat(session, chat_id, user)

    topic = body.topic.strip()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le thème de la revue de presse ne peut pas être vide.",
        )

    return await generate_review(session, chat, topic, llm, embed_model)


@router.get("/reviews", response_model=list[ReviewView])
def list_reviews(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[ReviewView]:
    """Liste les revues de presse de toutes les discussions de l'utilisateur."""
    statement = (
        select(Chat)
        .where(Chat.user_id == user.id, col(Chat.review_generated_at).is_not(None))
        .order_by(col(Chat.review_generated_at).desc())
    )
    return [to_review_view(chat) for chat in session.exec(statement).all()]
