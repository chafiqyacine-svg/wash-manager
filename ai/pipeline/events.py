"""Modèle d'événement + client HTTP vers le backend.

DOIT rester synchronisé avec `backend/app/schemas/event.py`.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from pipeline.outbox import Outbox


class EventType(str, Enum):
    ENTREE = "entree"
    ZONE_ENTER = "zone_enter"
    ZONE_EXIT = "zone_exit"
    SORTIE = "sortie"
    PLAQUE = "plaque"
    BADGE = "badge"


@dataclass
class Event:
    type: EventType
    track_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    camera_id: str | None = None
    zone: str | None = None
    plaque: str | None = None
    plaque_confiance: float | None = None
    badge_nfc_id: str | None = None
    couleur_gilet: str | None = None  # couleur de gilet détectée (hex) → identif. employé
    photo: str | None = None
    meta: dict | None = None

    def to_payload(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return {k: v for k, v in d.items() if v is not None}


class EventClient:
    """Envoie les événements au backend avec la clé d'ingestion.

    Si un `outbox` est fourni, l'envoi devient DURABLE : chaque événement est
    d'abord persisté localement puis retiré une fois acquitté. Rien n'est perdu
    en cas de coupure réseau, et l'ordre (FIFO) est préservé.
    """

    def __init__(self, events_url: str, api_key: str | None = None,
                 outbox: "Outbox | None" = None) -> None:
        self.events_url = events_url
        self.api_key = api_key or os.getenv("AI_INGEST_API_KEY", "")
        self._client = httpx.Client(timeout=5)
        self.outbox = outbox

    def _post(self, payload: dict) -> bool:
        """POST unitaire d'un payload déjà sérialisé. True si acquitté."""
        try:
            resp = self._client.post(
                self.events_url, json=payload, headers={"X-AI-Key": self.api_key}
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def send(self, event: Event) -> bool:
        """Envoie un événement. Avec outbox : persiste puis draine la file."""
        payload = event.to_payload()
        if self.outbox is None:
            return self._post(payload)
        # Durable : on empile d'abord (aucune perte), puis on tente de vider.
        self.outbox.ajouter(payload)
        self.flush()
        return True

    def flush(self) -> int:
        """Renvoie les événements en attente dans l'ordre. S'arrête au 1er échec
        (réseau encore coupé) pour préserver l'ordre FIFO. Renvoie le nombre
        d'événements acquittés.
        """
        if self.outbox is None:
            return 0
        envoyes = 0
        for id_, payload in self.outbox.en_attente():
            if self._post(payload):
                self.outbox.supprimer(id_)
                envoyes += 1
            else:
                self.outbox.incrementer_essai(id_)
                break  # réseau toujours indisponible : on réessaiera plus tard
        return envoyes

    def charger_palette_gilets(self, site_id: int | None = None) -> list[str]:
        """Récupère les couleurs de gilet enregistrées auprès du backend.

        Appelé au démarrage pour garder l'edge synchronisé avec les employés
        (au lieu d'une palette figée en config). Renvoie [] en cas d'échec :
        l'identification par gilet est alors simplement désactivée.
        """
        url = self.events_url.rstrip("/") + "/palette-gilets"
        params = {"site_id": site_id} if site_id else None
        try:
            resp = self._client.get(url, headers={"X-AI-Key": self.api_key}, params=params)
            resp.raise_for_status()
            return list(resp.json().get("couleurs", []))
        except httpx.HTTPError:
            return []
