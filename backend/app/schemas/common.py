"""Schémas Pydantic communs (véhicules, employés, forfaits, transactions…).

Squelette : les champs principaux sont présents. TODO(dev): compléter/valider
selon les besoins réels de l'UI (pagination, filtres, champs calculés).
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─── Auth ────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: str
    password: str


# ─── Forfaits ────────────────────────────────────────────────────────────────
class ForfaitBase(BaseModel):
    nom: str
    prix: float
    zones_requises: list[str]
    temps_min: int
    temps_max: int


class ForfaitOut(ORMModel, ForfaitBase):
    id: int


class ForfaitUpdate(BaseModel):
    """Mise à jour partielle d'un forfait depuis l'écran Configuration."""
    prix: float | None = None
    zones_requises: list[str] | None = None
    temps_min: int | None = None
    temps_max: int | None = None


class ForfaitCreate(ForfaitBase):
    """Création d'un nouveau service/forfait."""


# ─── Employés ────────────────────────────────────────────────────────────────
class EmployeBase(BaseModel):
    nom: str
    badge_nfc_id: str | None = None
    couleur_gilet: str | None = None
    date_embauche: date | None = None
    site_id: int | None = None
    actif: bool = True


class EmployeOut(ORMModel, EmployeBase):
    id: int


class EmployeCreate(EmployeBase):
    pass


class EmployeUpdate(BaseModel):
    nom: str | None = None
    badge_nfc_id: str | None = None
    couleur_gilet: str | None = None
    site_id: int | None = None
    actif: bool | None = None


# ─── Véhicules ───────────────────────────────────────────────────────────────
class VehiculeOut(ORMModel):
    id: int
    plaque: str
    premiere_visite: datetime | None
    derniere_visite: datetime | None
    nombre_visites: int


# ─── Transactions ────────────────────────────────────────────────────────────
class TransactionOut(ORMModel):
    id: int
    track_id: str | None
    vehicule_id: int | None
    employe_id: int | None
    forfait_id: int | None
    heure_entree: datetime | None
    heure_sortie: datetime | None
    duree_totale: int | None
    forfait_detecte: str | None
    conforme: bool | None
    statut: str


# ─── Anomalies ───────────────────────────────────────────────────────────────
class AnomalieOut(ORMModel):
    id: int
    transaction_id: int | None
    employe_id: int | None
    type: str
    severite: str
    description: str | None
    heure: datetime
    photo: str | None
    notifie: bool
    resolu: bool


# ─── POS (rapprochement ticket de caisse) ────────────────────────────────────
class TicketPOSIn(BaseModel):
    """Ticket envoyé par le système de caisse pour rapprochement avec un véhicule."""
    forfait: str                     # Rapide/Premium/Complet
    prix: float
    plaque: str | None = None        # si saisie en caisse
    heure: datetime
    reference: str | None = None     # n° de ticket POS
