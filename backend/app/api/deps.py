"""Dépendances FastAPI partagées : session DB, utilisateur courant, clé IA."""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, verify_ingest_key
from app.models import Utilisateur

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilisateur:
    sub = decode_access_token(token)
    if sub is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalide")
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == sub))
    if user is None or not user.actif:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur inconnu ou inactif")
    return user


def require_ingest_key(x_ai_key: str | None = Header(default=None)) -> None:
    """Protège l'endpoint d'ingestion (pipeline `ai/`)."""
    if not verify_ingest_key(x_ai_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clé d'ingestion IA invalide")
