from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()


class Chat(SQLModel, table=True):
    """Une discussion entre un utilisateur et l'agent NewsFoundry."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # Propriétaire de la discussion : sert à la vérification des autorisations
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Prompt système figé à la création de la discussion : il ne doit pas changer
    # d'un jour à l'autre pour garder la continuité d'une discussion déjà entamée.
    system_prompt: str = Field(sa_column=Column(Text, nullable=False))

    # Historique complet au format PydanticAI (sérialisé en JSON via
    # ModelMessagesTypeAdapter) : il est renvoyé tel quel au LLM à chaque message.
    messages: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
