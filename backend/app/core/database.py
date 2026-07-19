"""Connexion SQLAlchemy : engine, session, classe de base ORM."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles ORM."""


def get_db() -> Generator:
    """Dépendance FastAPI : fournit une session DB par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
