"""Tests du rapprochement transaction ↔ ticket de caisse (fonction pure)."""
from datetime import datetime, timedelta

from app.services.reconciliation import (
    InfoTransaction,
    TicketCandidat,
    choisir_ticket,
)

T0 = datetime(2026, 7, 19, 10, 0, 0)


def _txn(plaque=None, entree=T0):
    return InfoTransaction(plaque=plaque, heure_entree=entree, heure_sortie=None)


def test_match_exact_plaque():
    candidats = [
        TicketCandidat(id=1, plaque="99999-Z-9", heure=T0 - timedelta(minutes=25)),
        TicketCandidat(id=2, plaque="12345-A-67", heure=T0 - timedelta(minutes=5)),
    ]
    choisi = choisir_ticket(_txn(plaque="12345-A-67"), candidats)
    assert choisi.id == 2


def test_match_temporel_sans_plaque():
    candidats = [
        TicketCandidat(id=1, plaque=None, heure=T0 - timedelta(minutes=2)),
        TicketCandidat(id=2, plaque=None, heure=T0 - timedelta(minutes=20)),
    ]
    choisi = choisir_ticket(_txn(), candidats)
    assert choisi.id == 1  # le plus proche dans le temps


def test_aucun_candidat_dans_fenetre():
    candidats = [TicketCandidat(id=1, plaque=None, heure=T0 - timedelta(hours=3))]
    assert choisir_ticket(_txn(), candidats, fenetre_minutes=30) is None


def test_aucun_ticket():
    assert choisir_ticket(_txn(plaque="12345-A-67"), []) is None
