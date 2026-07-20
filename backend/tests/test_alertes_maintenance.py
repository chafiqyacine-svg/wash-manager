"""Tests d'intégration : alertes RH (retard/absence) et nettoyage orphelines."""
from datetime import date, datetime, timedelta, timezone

from app.models import Anomalie, Employe, HoraireEmploye, Transaction
from app.models.enums import AnomalieType
from app.services.alertes import scanner_absences, verifier_retard
from app.services.maintenance import nettoyer_transactions_orphelines


def test_alerte_retard(db, ref):
    e = Employe(nom="Ali", site_id=ref["site1"].id)
    db.add(e); db.flush()
    now = datetime.now(timezone.utc)
    db.add(HoraireEmploye(employe_id=e.id, jour=now.date().weekday(),
                          debut=(now - timedelta(minutes=40)).time().replace(second=0, microsecond=0),
                          fin=(now + timedelta(hours=4)).time().replace(second=0, microsecond=0)))
    db.commit()
    alerte = verifier_retard(db, e.id, now)   # ~40 min de retard
    assert alerte is not None
    assert alerte.type == AnomalieType.RETARD.value
    assert alerte.employe_id == e.id


def test_pas_dalerte_si_a_lheure(db, ref):
    e = Employe(nom="Sara", site_id=ref["site1"].id)
    db.add(e); db.flush()
    now = datetime.now(timezone.utc)
    db.add(HoraireEmploye(employe_id=e.id, jour=now.date().weekday(),
                          debut=(now - timedelta(minutes=2)).time().replace(second=0, microsecond=0),
                          fin=(now + timedelta(hours=4)).time().replace(second=0, microsecond=0)))
    db.commit()
    assert verifier_retard(db, e.id, now) is None


def test_scan_absence_une_seule_alerte(db, ref):
    e = Employe(nom="Nabil", site_id=ref["site1"].id)
    db.add(e); db.flush()
    now = datetime.now(timezone.utc)
    db.add(HoraireEmploye(employe_id=e.id, jour=now.date().weekday(),
                          debut=(now - timedelta(minutes=60)).time().replace(second=0, microsecond=0),
                          fin=(now + timedelta(hours=4)).time().replace(second=0, microsecond=0)))
    db.commit()
    scanner_absences(db, now)
    scanner_absences(db, now)   # 2e passage : pas de doublon
    n = db.query(Anomalie).filter(Anomalie.type == AnomalieType.ABSENCE.value,
                                  Anomalie.employe_id == e.id).count()
    assert n == 1


def test_nettoyage_orphelines(db, ref):
    now = datetime.now(timezone.utc)
    db.add(Transaction(statut="en_cours", heure_entree=now - timedelta(hours=6)))  # orpheline
    db.add(Transaction(statut="en_cours", heure_entree=now - timedelta(minutes=5)))  # récente
    db.commit()
    n = nettoyer_transactions_orphelines(db, now)
    assert n == 1
    assert db.query(Transaction).filter(Transaction.statut == "en_cours").count() == 1
    assert db.query(Transaction).filter(Transaction.statut == "abandonnee").count() == 1
