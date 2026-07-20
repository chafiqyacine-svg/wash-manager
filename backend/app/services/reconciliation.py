"""Rapprochement transaction (IA) ↔ ticket de caisse (forfait payé).

Remplace le connecteur POS externe : la source du « forfait payé » est la table
`tickets` alimentée par la caisse intégrée.

Stratégie de matching (fonction pure, testable sans DB) :
  1. Si la transaction a une plaque ET qu'un ticket ouvert porte la même plaque
     -> match certain.
  2. Sinon, on prend le ticket ouvert le plus proche dans le temps (autour de
     l'heure d'entrée/sortie) dans une fenêtre configurable.
  3. Aucun candidat -> None (=> anomalie « lavage non facturé » côté appelant).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise en UTC-aware pour comparer sereinement naïf et aware
    (SQLite renvoie des datetimes naïfs, PostgreSQL des datetimes aware)."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class TicketCandidat:
    id: int
    plaque: str | None
    heure: datetime


@dataclass
class InfoTransaction:
    plaque: str | None
    heure_entree: datetime | None
    heure_sortie: datetime | None

    @property
    def heure_reference(self) -> datetime | None:
        return self.heure_entree or self.heure_sortie


def choisir_ticket(
    txn: InfoTransaction,
    candidats: list[TicketCandidat],
    fenetre_minutes: int = 30,
) -> TicketCandidat | None:
    if not candidats:
        return None

    # 1) Match exact par plaque
    if txn.plaque:
        exacts = [c for c in candidats if c.plaque and c.plaque == txn.plaque]
        if exacts:
            # le plus proche dans le temps parmi les plaques identiques
            return _plus_proche(txn.heure_reference, exacts) or exacts[0]

    # 2) Match temporel dans la fenêtre
    ref = _aware(txn.heure_reference)
    if ref is None:
        return None
    fenetre = timedelta(minutes=fenetre_minutes)
    dans_fenetre = [c for c in candidats if abs(_aware(c.heure) - ref) <= fenetre]
    return _plus_proche(ref, dans_fenetre)


def _plus_proche(ref: datetime | None, candidats: list[TicketCandidat]) -> TicketCandidat | None:
    ref = _aware(ref)
    if ref is None or not candidats:
        return None
    return min(candidats, key=lambda c: abs(_aware(c.heure) - ref))
