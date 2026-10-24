"""Configuration commune des tests.

- Base SQLite en mémoire : rapide, isolée, sans Docker (en CI comme en local).
- Aucun vrai LLM : `ALLOW_MODEL_REQUESTS = False` fait échouer tout appel réseau
  vers un modèle, et le modèle est remplacé par un `TestModel` de PydanticAI.
"""

import os

# Variables d'environnement définies AVANT l'import de l'application,
# car config.py les lit au moment de l'import.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "secret-de-test-suffisamment-long-pour-hs256")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic_ai import models  # noqa: E402
from pydantic_ai.models.test import TestModel  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from database import get_session  # noqa: E402
from dependencies import get_chat_model  # noqa: E402
from main import app  # noqa: E402
from models import User  # noqa: E402
from security import create_access_token, hash_password  # noqa: E402

models.ALLOW_MODEL_REQUESTS = False

FAKE_LLM_ANSWER = "Réponse de test de l'agent."


@pytest.fixture
def session():
    # StaticPool : toutes les connexions partagent la même base en mémoire
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    # Le vrai LLM est remplacé par le TestModel de PydanticAI (réponse fixe)
    app.dependency_overrides[get_chat_model] = lambda: TestModel(
        custom_output_text=FAKE_LLM_ANSWER
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def _create_user(session: Session, email: str) -> User:
    user = User(email=email, hashed_password=hash_password("motdepasse"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def alice(session: Session) -> User:
    return _create_user(session, "alice@test.com")


@pytest.fixture
def bob(session: Session) -> User:
    return _create_user(session, "bob@test.com")


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}
