"""Routes des discussions. Toutes nécessitent un utilisateur authentifié."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai.models import Model
from sqlmodel import Session, col, select

from database import get_session
from dependencies import get_chat_model, get_current_user, get_news_client
from models import Chat, User
from schemas import ChatDetail, ChatSummary, MessageView, SendMessageRequest
from services.chat_service import (
    build_system_prompt_with_news,
    get_owned_chat,
    load_history,
    send_message,
    to_message_views,
)
from services.news_api import NewsClient

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatSummary])
def list_chats(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Chat]:
    """Liste les discussions de l'utilisateur connecté, les plus récentes d'abord."""
    statement = (
        select(Chat).where(Chat.user_id == user.id).order_by(col(Chat.updated_at).desc())
    )
    return list(session.exec(statement).all())


@router.post("", response_model=ChatSummary, status_code=status.HTTP_201_CREATED)
async def create_chat(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    news_client: NewsClient = Depends(get_news_client),
) -> Chat:
    """Crée une nouvelle discussion et retourne son identifiant.

    Le prompt système, qui contient les actualités du jour, est construit une
    seule fois ici puis sauvegardé : la discussion garde le même contexte même
    si on la reprend un autre jour.
    """
    system_prompt = await build_system_prompt_with_news(news_client)
    chat = Chat(user_id=user.id, system_prompt=system_prompt)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(
    chat_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ChatDetail:
    """Retourne l'historique d'une discussion de l'utilisateur."""
    chat = get_owned_chat(session, chat_id, user)
    return ChatDetail(
        id=chat.id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=to_message_views(load_history(chat)),
    )


@router.post("/{chat_id}/messages", response_model=MessageView)
async def post_message(
    chat_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    llm: Model = Depends(get_chat_model),
) -> MessageView:
    """Ajoute un message utilisateur à la discussion et retourne la réponse du LLM."""
    chat = get_owned_chat(session, chat_id, user)

    content = body.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le message ne peut pas être vide.",
        )

    return await send_message(session, chat, content, llm)
