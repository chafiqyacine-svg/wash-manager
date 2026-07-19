"""Tests de la logique métier déterministe (classification + anomalies).

Logique pilotée par la base (ForfaitDef) — testée sans base de données.
Lancer : `pytest backend/tests`.
"""
from app.models.enums import AnomalieType
from app.services.anomalie import ContexteTransaction, detecter_anomalies
from app.services.classification import (
    ForfaitDef,
    deduire_forfait_effectue,
    est_conforme,
)

RAPIDE = ForfaitDef("Rapide", frozenset({"B"}), 10, 30)
PREMIUM = ForfaitDef("Premium", frozenset({"B", "C"}), 20, 60)
COMPLET = ForfaitDef("Complet", frozenset({"B", "C", "D"}), 35, 100)
# Service personnalisé ajouté par le gérant (prouve le pilotage par la base).
VIP = ForfaitDef("VIP", frozenset({"B", "C", "D"}), 50, 150)
TOUS = [RAPIDE, PREMIUM, COMPLET, VIP]


def test_deduction_forfait_complet():
    # B,C,D → le plus riche à ce prix est VIP (150) devant Complet (100).
    assert deduire_forfait_effectue({"B", "C", "D"}, [RAPIDE, PREMIUM, COMPLET]) is COMPLET
    assert deduire_forfait_effectue({"B", "C", "D"}, TOUS) is VIP


def test_deduction_forfait_premium():
    assert deduire_forfait_effectue({"B", "C"}, TOUS) is PREMIUM


def test_deduction_forfait_rapide():
    assert deduire_forfait_effectue({"B"}, TOUS) is RAPIDE


def test_deduction_aucune_zone():
    assert deduire_forfait_effectue(set(), TOUS) is None


def test_conformite_ok():
    assert est_conforme(COMPLET, {"B", "C", "D"}, 40) is True


def test_conformite_ko_zone_manquante():
    assert est_conforme(COMPLET, {"B", "C"}, 40) is False


def test_conformite_ko_duree():
    assert est_conforme(PREMIUM, {"B", "C"}, 5) is False


def test_anomalie_forfait_non_respecte():
    ctx = ContexteTransaction(
        forfait_paye=COMPLET, forfait_detecte=RAPIDE,
        zones_visitees={"B"}, duree_totale_min=8, plaque_lue=True,
    )
    types = {a.type for a in detecter_anomalies(ctx)}
    assert AnomalieType.FORFAIT_NON_RESPECTE in types


def test_anomalie_lavage_non_facture():
    ctx = ContexteTransaction(
        forfait_paye=None, forfait_detecte=PREMIUM,
        zones_visitees={"B", "C"}, duree_totale_min=25, plaque_lue=True,
    )
    assert {a.type for a in detecter_anomalies(ctx)} == {AnomalieType.LAVAGE_NON_FACTURE}


def test_anomalie_ticket_fantome():
    ctx = ContexteTransaction(
        forfait_paye=RAPIDE, forfait_detecte=None,
        zones_visitees=set(), duree_totale_min=None, plaque_lue=False,
    )
    assert {a.type for a in detecter_anomalies(ctx)} == {AnomalieType.TICKET_FANTOME}


def test_service_personnalise_conforme():
    # Un service ajouté par le gérant fonctionne de bout en bout.
    assert est_conforme(VIP, {"B", "C", "D"}, 55) is True
    assert est_conforme(VIP, {"B", "C", "D"}, 40) is False  # < temps_min 50
