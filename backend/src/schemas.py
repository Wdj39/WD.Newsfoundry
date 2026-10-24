"""Schémas Pydantic des corps de requêtes et de réponses de l'API."""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


def _assume_utc(value: datetime) -> datetime:
    """Les dates sont enregistrées en UTC, mais PostgreSQL (colonnes sans fuseau)
    les relit sans fuseau horaire. On le rajoute pour que le JSON contienne
    « +00:00 » et que le navigateur les convertisse correctement en heure locale."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


UTCDatetime = Annotated[datetime, AfterValidator(_assume_utc)]


# --- Authentification ---


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str


# --- Discussions ---


class MessageView(BaseModel):
    """Message tel qu'affiché dans l'interface (sans les détails internes du LLM)."""

    role: Literal["user", "assistant"]
    content: str
    created_at: UTCDatetime


class ChatSummary(BaseModel):
    """Élément de la liste des discussions (barre latérale)."""

    id: int
    created_at: UTCDatetime
    updated_at: UTCDatetime


class ChatDetail(ChatSummary):
    messages: list[MessageView]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


# --- Revues de presse ---


class GenerateReviewRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)


class ReviewArticleView(BaseModel):
    title: str
    source: str
    url: str
    summary: str


class ReviewView(BaseModel):
    chat_id: int
    topic: str
    title: str
    summary: str
    articles: list[ReviewArticleView]
    generated_at: UTCDatetime | None
