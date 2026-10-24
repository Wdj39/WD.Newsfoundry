from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine, select

from config import DATABASE_URL
from models import User
from security import hash_password

engine = create_engine(DATABASE_URL)


def init_db() -> None:
    """Crée les tables et l'utilisateur de test s'ils n'existent pas."""
    SQLModel.metadata.create_all(engine)
    print("Database initialized successfully")

    # Création de l'utilisateur par défaut (pas de page d'inscription dans cette V1)
    default_email = "test@test.com"
    default_password = "test"

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == default_email)).first()

        if not user:
            session.add(
                User(email=default_email, hashed_password=hash_password(default_password))
            )
            session.commit()


def get_session() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session de base de données par requête."""
    with Session(engine) as session:
        yield session
