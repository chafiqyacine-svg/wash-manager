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


def require_role(*roles: str):
    """Fabrique une dépendance exigeant l'un des rôles donnés."""
    def dependance(user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé (rôle insuffisant)")
        return user
    return dependance


def resolve_site(
    site_id: int | None = None,
    user: Utilisateur = Depends(get_current_user),
) -> int | None:
    """Résout le site effectif d'une requête (sécurité multi-site).

    - admin (ou compte non rattaché à un site) : le `site_id` demandé passe tel
      quel (peut tout voir / filtrer librement) ;
    - manager/caissier rattaché à un site : FORCÉ à son site, quel que soit le
      `site_id` demandé — il ne peut voir que son emplacement.
    """
    if user.role != "admin" and user.site_id is not None:
        return user.site_id
    return site_id
