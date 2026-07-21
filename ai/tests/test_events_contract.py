"""Contrat d'événement IA → backend.

Garde-fou de synchronisation : le payload émis par le pipeline ne doit contenir
que des champs connus du schéma `EventIn` du backend, et doit pouvoir porter
tous les signaux produits par le edge (plaque, gilet, badge…).
"""
from datetime import datetime, timezone

from pipeline.events import Event, EventType

# Champs acceptés par backend/app/schemas/event.py::EventIn (source de vérité).
# À mettre à jour EN MIROIR si le schéma backend change.
CHAMPS_BACKEND = {
    "type", "track_id", "camera_id", "zone", "timestamp",
    "plaque", "plaque_confiance", "badge_nfc_id", "couleur_gilet",
    "photo", "meta",
}


def test_payload_sous_ensemble_du_contrat_backend():
    ev = Event(
        type=EventType.PLAQUE, track_id="v1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        plaque="12345-A-67", plaque_confiance=0.9,
    )
    assert set(ev.to_payload()) <= CHAMPS_BACKEND


def test_couleur_gilet_transportable():
    """Régression : le gilet détecté doit pouvoir être émis (EventIn.couleur_gilet)."""
    ev = Event(type=EventType.BADGE, track_id="v1", couleur_gilet="#E11D48")
    payload = ev.to_payload()
    assert payload["couleur_gilet"] == "#E11D48"
    assert "couleur_gilet" in CHAMPS_BACKEND


def test_to_payload_omet_les_none():
    ev = Event(type=EventType.SORTIE, track_id="v1")
    payload = ev.to_payload()
    assert "plaque" not in payload and "zone" not in payload
    assert payload["type"] == "sortie"
