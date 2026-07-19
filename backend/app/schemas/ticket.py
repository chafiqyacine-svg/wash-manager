"""Schémas de la caisse intégrée (tickets)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketCreate(BaseModel):
    """Saisie caisse au moment de l'encaissement."""
    forfait_id: int
    plaque: str | None = None      # facultatif mais recommandé (meilleur rapprochement)
    employe_id: int | None = None  # caissier
    reference: str | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    forfait_id: int
    prix: float
    plaque: str | None
    employe_id: int | None
    reference: str | None
    heure: datetime
    statut: str
    transaction_id: int | None
