"""Authentification du dashboard (JWT)."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import Utilisateur
from app.schemas.common import Token
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    # OAuth2PasswordRequestForm utilise `username` — on y met l'email.
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == form.username))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    return Token(access_token=create_access_token(subject=user.email))


@router.get("/me", response_model=UserOut)
def me(user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Profil courant (rôle + site) — permet au frontend d'adapter l'UI."""
    return user
