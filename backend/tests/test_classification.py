"""Tests de la logique métier déterministe (classification + anomalies).

Ces tests couvrent le cœur spécifié au cahier des charges. Ils tournent sans
base de données. Lancer : `pytest backend/tests`.
"""
from app.models.enums import AnomalieType, ForfaitNom
from app.services.anomalie import ContexteTransaction, detecter_anomalies
from app.services.classification import (
    ParcoursVehicule,
    deduire_forfait_effectue,
    est_conforme,
)


def test_deduction_forfait_complet():
    p = ParcoursVehicule(zones_visitees={"B", "C", "D"}, duree_totale_min=45)
    assert deduire_forfait_effectue(p) is ForfaitNom.COMPLET


def test_deduction_forfait_premium():
    p = ParcoursVehicule(zones_visitees={"B", "C"}, duree_totale_min=30)
    assert deduire_forfait_effectue(p) is ForfaitNom.PREMIUM


def test_deduction_forfait_rapide():
    p = ParcoursVehicule(zones_visitees={"B"}, duree_totale_min=12)
    assert deduire_forfait_effectue(p) is ForfaitNom.RAPIDE


def test_conformite_ok():
    p = ParcoursVehicule(zones_visitees={"B", "C", "D"}, duree_totale_min=40)
    assert est_conforme(ForfaitNom.COMPLET, p, temps_min_paye=35) is True


def test_conformite_ko_zone_manquante():
    p = ParcoursVehicule(zones_visitees={"B", "C"}, duree_totale_min=40)
    assert est_conforme(ForfaitNom.COMPLET, p, temps_min_paye=35) is False


def test_anomalie_forfait_non_respecte():
    ctx = ContexteTransaction(
        forfait_paye=ForfaitNom.COMPLET,
        forfait_detecte=ForfaitNom.RAPIDE,
        zones_visitees={"B"},
        duree_totale_min=8,
        plaque_lue=True,
    )
    types = {a.type for a in detecter_anomalies(ctx)}
    assert AnomalieType.FORFAIT_NON_RESPECTE in types


def test_anomalie_lavage_non_facture():
    ctx = ContexteTransaction(
        forfait_paye=None,
        forfait_detecte=ForfaitNom.PREMIUM,
        zones_visitees={"B", "C"},
        duree_totale_min=25,
        plaque_lue=True,
    )
    types = {a.type for a in detecter_anomalies(ctx)}
    assert types == {AnomalieType.LAVAGE_NON_FACTURE}


def test_anomalie_ticket_fantome():
    ctx = ContexteTransaction(
        forfait_paye=ForfaitNom.RAPIDE,
        forfait_detecte=None,
        zones_visitees=set(),
        duree_totale_min=None,
        plaque_lue=False,
    )
    types = {a.type for a in detecter_anomalies(ctx)}
    assert types == {AnomalieType.TICKET_FANTOME}
