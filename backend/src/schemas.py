"""Schémas Pydantic des corps de requêtes et de réponses de l'API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    created_at: datetime


class ChatSummary(BaseModel):
    """Élément de la liste des discussions (barre latérale)."""

    id: int
    created_at: datetime
    updated_at: datetime


class ChatDetail(ChatSummary):
    messages: list[MessageView]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
