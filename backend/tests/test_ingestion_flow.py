"""Tests d'intégration du pipeline d'ingestion (avec base de données)."""
from datetime import datetime, timezone

from sqlalchemy import select

from app.models import (
    Anomalie,
    Employe,
    ForfaitProduit,
    Produit,
    Ticket,
    Transaction,
    Vehicule,
)
from app.models.enums import AnomalieType
from app.schemas.event import EventIn, EventType
from app.services.ingestion import consommer_inventaire, finaliser_transaction, traiter_evenement


def _ev(type_, track="v1", **kw):
    return EventIn(type=type_, track_id=track, timestamp=datetime.now(timezone.utc), **kw)


def _active(db, track):
    return db.scalar(select(Transaction).where(
        Transaction.track_id == track, Transaction.statut == "en_cours"))


def _parcours(db, track="v1", plaque="12345-A-67", zones=("B", "C"), bay_id=None):
    """Joue un passage véhicule complet via les événements."""
    traiter_evenement(db, _ev(EventType.ENTREE, track))
    if plaque:
        traiter_evenement(db, _ev(EventType.PLAQUE, track, plaque=plaque, plaque_confiance=0.9))
    txn = _active(db, track)
    if bay_id:
        txn.bay_id = bay_id
        db.commit()
    for z in zones:
        traiter_evenement(db, _ev(EventType.ZONE_ENTER, track, zone=z))
        traiter_evenement(db, _ev(EventType.ZONE_EXIT, track, zone=z))
    traiter_evenement(db, _ev(EventType.SORTIE, track))
    return db.scalar(select(Transaction).where(Transaction.track_id == track))


def test_flux_complet_cree_transaction_et_vehicule(db, ref):
    txn = _parcours(db, zones=("B", "C"))
    assert txn.statut == "cloturee"
    assert txn.forfait_detecte == "Premium"          # zones B+C
    assert db.scalar(select(Vehicule).where(Vehicule.plaque == "12345-A-67")) is not None


def test_lavage_non_facture_leve_anomalie(db, ref):
    txn = _parcours(db, zones=("B",))
    types = {a.type for a in db.query(Anomalie).filter(Anomalie.transaction_id == txn.id)}
    assert AnomalieType.LAVAGE_NON_FACTURE.value in types


def test_rapprochement_ticket_rend_conforme(db, ref):
    # Ticket payé Premium, même plaque -> rapproché, conforme.
    db.add(Ticket(forfait_id=ref["premium"].id, prix=60, plaque="12345-A-67",
                  heure=datetime.now(timezone.utc), statut="ouvert"))
    db.commit()
    txn = _parcours(db, zones=("B", "C"), bay_id=ref["bay"].id)
    db.refresh(txn)
    assert txn.forfait_id == ref["premium"].id
    assert txn.conforme is True
    ticket = db.query(Ticket).first()
    assert ticket.statut == "rapproche"


def test_forfait_non_respecte(db, ref):
    # Complet payé mais seulement B effectué -> anomalie critique.
    db.add(Ticket(forfait_id=ref["complet"].id, prix=100, plaque="12345-A-67",
                  heure=datetime.now(timezone.utc), statut="ouvert"))
    db.commit()
    txn = _parcours(db, zones=("B",), bay_id=ref["bay"].id)
    types = {a.type for a in db.query(Anomalie).filter(Anomalie.transaction_id == txn.id)}
    assert AnomalieType.FORFAIT_NON_RESPECTE.value in types
    assert txn.conforme is False


def test_track_id_reutilise_cible_la_transaction_recente(db, ref):
    """Deux 'en_cours' avec le même track_id (SORTIE manquée + réattribution) :
    les événements suivants ciblent la transaction la PLUS RÉCENTE."""
    traiter_evenement(db, _ev(EventType.ENTREE, "7"))       # 1er véhicule (SORTIE ratée)
    ancienne = _active(db, "7")
    traiter_evenement(db, _ev(EventType.ENTREE, "7"))       # 2e véhicule, id réattribué
    recente = db.scalars(select(Transaction).where(Transaction.track_id == "7")
                         .order_by(Transaction.id.desc())).first()
    assert recente.id != ancienne.id

    # Une zone puis la sortie doivent s'appliquer à la transaction récente.
    traiter_evenement(db, _ev(EventType.ZONE_ENTER, "7", zone="B"))
    traiter_evenement(db, _ev(EventType.SORTIE, "7"))
    db.refresh(ancienne); db.refresh(recente)
    assert recente.statut == "cloturee"
    assert recente.zone_b_debut is not None
    assert ancienne.statut == "en_cours"      # l'ancienne n'est pas touchée
    assert ancienne.zone_b_debut is None


def test_identification_employe_par_gilet(db, ref):
    """Événement BADGE porteur de couleur_gilet → l'employé est rattaché à la txn.

    Reproduit le flux edge : l'orchestrateur émet la couleur canonique, le
    backend la rapproche (exact) de l'employé au gilet correspondant.
    """
    emp = Employe(nom="Karim", site_id=ref["site1"].id, couleur_gilet="#E11D48")
    db.add(emp); db.commit()

    traiter_evenement(db, _ev(EventType.ENTREE, "v9"))
    traiter_evenement(db, _ev(EventType.BADGE, "v9", couleur_gilet="#E11D48"))
    txn = _active(db, "v9")
    assert txn.employe_id == emp.id


def test_gilet_inconnu_nassocie_personne(db, ref):
    db.add(Employe(nom="Karim", site_id=ref["site1"].id, couleur_gilet="#E11D48"))
    db.commit()
    traiter_evenement(db, _ev(EventType.ENTREE, "v10"))
    traiter_evenement(db, _ev(EventType.BADGE, "v10", couleur_gilet="#000000"))
    assert _active(db, "v10").employe_id is None


def test_consommation_stock_idempotente(db, ref):
    cire = Produit(site_id=ref["site1"].id, nom="Cire", unite="L", quantite=8, seuil_alerte=2)
    db.add(cire)
    db.flush()
    db.add(ForfaitProduit(forfait_id=ref["premium"].id, produit_id=cire.id, lavages_par_unite=4))
    db.commit()

    txn = Transaction(forfait_id=ref["premium"].id, bay_id=ref["bay"].id, statut="cloturee",
                      heure_entree=datetime.now(timezone.utc))
    db.add(txn)
    db.flush()
    consommer_inventaire(db, txn)          # -0.25
    consommer_inventaire(db, txn)          # rappel : ne doit PAS re-décrémenter
    db.commit()
    db.refresh(cire)
    assert float(cire.quantite) == 7.75
    assert txn.inventaire_consomme is True


def test_finaliser_ne_double_pas_la_consommation(db, ref):
    cire = Produit(site_id=ref["site1"].id, nom="Cire", unite="L", quantite=10, seuil_alerte=2)
    db.add(cire); db.flush()
    db.add(ForfaitProduit(forfait_id=ref["premium"].id, produit_id=cire.id, lavages_par_unite=2))
    db.commit()
    txn = Transaction(forfait_id=ref["premium"].id, bay_id=ref["bay"].id, statut="cloturee",
                      heure_entree=datetime.now(timezone.utc))
    db.add(txn); db.flush()
    finaliser_transaction(db, txn, None); db.commit()
    q1 = float(db.get(Produit, cire.id).quantite)
    finaliser_transaction(db, txn, None); db.commit()   # rapprochement manuel simulé
    q2 = float(db.get(Produit, cire.id).quantite)
    assert q1 == q2 == 9.5
