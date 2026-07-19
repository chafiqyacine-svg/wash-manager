"""Gestion des utilisateurs (réservée aux administrateurs)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.security import hash_password
from app.models import Utilisateur
from app.models.enums import Role
from app.schemas.user import UserCreate, UserOut, UserUpdate

# Toutes les routes exigent le rôle admin.
router = APIRouter(prefix="/users", tags=["users"],
                   dependencies=[Depends(require_role(Role.ADMIN.value))])


@router.get("", response_model=list[UserOut])
def lister(db: Session = Depends(get_db)):
    return db.scalars(select(Utilisateur)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def creer(payload: UserCreate, db: Session = Depends(get_db)) -> Utilisateur:
    if db.scalar(select(Utilisateur).where(Utilisateur.email == payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email déjà utilisé")
    if payload.role not in {r.value for r in Role}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rôle invalide")
    user = Utilisateur(
        email=payload.email, nom=payload.nom, role=payload.role,
        site_id=payload.site_id, hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def modifier(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> Utilisateur:
    user = db.get(Utilisateur, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur inconnu")
    data = payload.model_dump(exclude_none=True)
    if "role" in data and data["role"] not in {r.value for r in Role}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rôle invalide")
    if "password" in data:
        user.hashed_password = hash_password(data.pop("password"))
    for champ, valeur in data.items():
        setattr(user, champ, valeur)
    db.commit()
    db.refresh(user)
    return user
