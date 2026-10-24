from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Heure actuelle en UTC, sans fuseau horaire.

    Les colonnes de date sont de type « timestamp without time zone » : si on y
    enregistre une date avec fuseau, PostgreSQL la convertit d'abord dans le fuseau
    de sa session (qui dépend de la configuration du serveur). En stockant une
    heure UTC « naïve », la valeur enregistrée ne dépend plus de ce réglage.
    Le fuseau UTC est rajouté à la lecture (voir schemas.UTCDatetime).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


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

    # Articles chargés pendant la discussion (gros titres du jour + résultats de
    # search_news), avec leur contenu complet : source du RAG de la revue de presse.
    # Format : [{"title", "summary", "url", "publish_date", "text"}, ...]
    loaded_articles: Optional[list[dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )

    # --- Revue de presse générée à partir de la discussion (vide tant qu'aucune
    # revue n'a été générée ; une nouvelle génération remplace la précédente) ---
    review_topic: Optional[str] = Field(default=None)
    review_title: Optional[str] = Field(default=None)
    review_summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    # Liste d'articles : [{"title", "source", "url", "summary"}, ...]
    review_articles: Optional[list[dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    review_generated_at: Optional[datetime] = Field(default=None)
