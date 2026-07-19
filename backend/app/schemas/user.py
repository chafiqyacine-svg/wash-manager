"""Schémas des utilisateurs (comptes du dashboard)."""
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nom: str
    role: str
    site_id: int | None
    actif: bool


class UserCreate(BaseModel):
    email: str
    nom: str
    password: str
    role: str = "manager"          # admin | manager | caissier
    site_id: int | None = None     # requis pour manager/caissier


class UserUpdate(BaseModel):
    nom: str | None = None
    role: str | None = None
    site_id: int | None = None
    actif: bool | None = None
    password: str | None = None
