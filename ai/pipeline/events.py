"""Modèle d'événement + client HTTP vers le backend.

DOIT rester synchronisé avec `backend/app/schemas/event.py`.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum

import httpx


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
    photo: str | None = None
    meta: dict | None = None

    def to_payload(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return {k: v for k, v in d.items() if v is not None}


class EventClient:
    """Envoie les événements au backend avec la clé d'ingestion."""

    def __init__(self, events_url: str, api_key: str | None = None) -> None:
        self.events_url = events_url
        self.api_key = api_key or os.getenv("AI_INGEST_API_KEY", "")
        self._client = httpx.Client(timeout=5)

    def send(self, event: Event) -> bool:
        headers = {"X-AI-Key": self.api_key}
        try:
            resp = self._client.post(self.events_url, json=event.to_payload(), headers=headers)
            resp.raise_for_status()
            return True
        except httpx.HTTPError:
            # TODO(dev): file de retry locale (SQLite/queue) en cas de coupure réseau
            #   pour ne perdre aucun événement.
            return False
