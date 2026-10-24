"""Dépendances FastAPI partagées entre les routes."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic_ai.models import Model
from sqlmodel import Session

from agents.llm import LLMNotConfiguredError, get_llm
from database import get_session
from models import User
from security import decode_access_token
from services.news_api import NewsClient
from services.rag import EmbeddingNotConfiguredError, get_embedding_model

# auto_error=False : on gère nous-mêmes l'absence de token pour renvoyer un 401
# avec un message clair (par défaut FastAPI renverrait un 403).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Retourne l'utilisateur authentifié à partir du header `Authorization: Bearer <token>`."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session invalide ou expirée, veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized

    user = session.get(User, user_id)
    if user is None:
        # Le token est valide mais l'utilisateur a été supprimé entre-temps.
        raise unauthorized

    return user


def get_chat_model() -> Model:
    """Fournit le modèle de langage aux routes.

    Passer par une dépendance FastAPI permet aux tests de le remplacer par un
    `TestModel` de PydanticAI (`app.dependency_overrides`), sans aucun appel réseau.
    """
    try:
        return get_llm()
    except LLMNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le service d'IA n'est pas configuré sur le serveur.",
        )


def get_news_client() -> NewsClient:
    """Fournit le client World News API (remplacé par un faux client dans les tests)."""
    return NewsClient()


def get_embedding_model_or_none() -> BaseEmbedding | None:
    """Modèle d'embedding du RAG, ou None s'il n'est pas configuré
    (la revue de presse est alors générée sans RAG)."""
    try:
        return get_embedding_model()
    except EmbeddingNotConfiguredError:
        return None
