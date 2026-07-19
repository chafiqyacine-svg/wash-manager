"""Contrat d'événement pipeline IA → backend.

C'EST L'INTERFACE CENTRALE entre `ai/` et `backend/`. Le pipeline edge envoie un
événement à chaque fait marquant (franchissement de ligne, entrée/sortie de zone,
lecture de plaque, badge NFC). Le backend (services/ingestion.py) applique ces
événements à la transaction correspondante (identifiée par `track_id`).

Garder ce schéma synchronisé avec `ai/pipeline/events.py`.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    ENTREE = "entree"              # franchissement ligne d'entrée -> ouvre la transaction
    ZONE_ENTER = "zone_enter"      # le véhicule entre dans une zone (B/C/D)
    ZONE_EXIT = "zone_exit"        # le véhicule quitte une zone (B/C/D)
    SORTIE = "sortie"              # franchissement ligne de sortie -> clôture
    PLAQUE = "plaque"              # résultat LPR (peut arriver après l'entrée)
    BADGE = "badge"                # un employé a badgé (NFC) sur un poste


class EventIn(BaseModel):
    """Événement unitaire émis par le pipeline IA."""
    type: EventType
    track_id: str = Field(..., description="Identifiant de suivi du véhicule (tracker)")
    camera_id: str | None = Field(None, description="Caméra source")
    zone: str | None = Field(None, description="Code zone A-E (pour zone_enter/zone_exit)")
    timestamp: datetime = Field(..., description="Horodatage de l'événement (UTC)")

    # Charge utile selon le type d'événement
    plaque: str | None = Field(None, description="Plaque lue (type=plaque)")
    plaque_confiance: float | None = Field(None, description="Score OCR 0-1")
    badge_nfc_id: str | None = Field(None, description="Badge employé (type=badge)")
    photo: str | None = Field(None, description="Chemin/URL de la capture associée")

    # Champ libre pour extensions (ex: bbox, vitesse…) sans casser le contrat
    meta: dict | None = None


class EventAck(BaseModel):
    """Réponse du backend après ingestion d'un événement."""
    ok: bool
    transaction_id: int | None = None
    message: str | None = None
