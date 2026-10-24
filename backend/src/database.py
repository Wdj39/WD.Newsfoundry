import logging
from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from config import DATABASE_URL
from models import User
from security import hash_password

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)


def add_missing_columns() -> None:
    """Ajoute aux tables existantes les colonnes ajoutées depuis dans les modèles.

    `create_all` crée les tables manquantes mais ne modifie jamais une table qui
    existe déjà. Cette mini-migration ajoute les nouvelles colonnes (toutes
    facultatives) pour faire évoluer la base sans perdre les données.
    Pour un projet plus important, on utiliserait un outil dédié comme Alembic.
    """
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in SQLModel.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing or not column.nullable:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                connection.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}')
                )
                logger.info("Colonne ajoutée : %s.%s", table.name, column.name)


def init_db() -> None:
    """Crée les tables et l'utilisateur de test s'ils n'existent pas."""
    SQLModel.metadata.create_all(engine)
    add_missing_columns()
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
