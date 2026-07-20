"""Tests d'intégration présence / ponctualité (avec base de données)."""
from datetime import date, datetime, time, timedelta, timezone

from app.models import Employe, HoraireEmploye, Pointage
from app.services.presence import presence_du_jour


def _ligne(db, employe_id):
    for l in presence_du_jour(db, date.today()):
        if l["employe_id"] == employe_id:
            return l
    return None


def test_present_a_lheure(db, ref):
    e = Employe(nom="Ali", site_id=ref["site1"].id)
    db.add(e); db.flush()
    now = datetime.now(timezone.utc)
    debut = (now - timedelta(minutes=90))
    db.add(HoraireEmploye(employe_id=e.id, jour=date.today().weekday(),
                          debut=debut.time().replace(second=0, microsecond=0),
                          fin=(now + timedelta(hours=4)).time().replace(second=0, microsecond=0)))
    db.add(Pointage(employe_id=e.id, type="arrivee", heure=debut + timedelta(minutes=2)))
    db.commit()
    l = _ligne(db, e.id)
    assert l["statut"] == "present"
    assert l["retard_min"] is not None and l["retard_min"] <= 3
    assert l["temps_present_min"] and l["temps_present_min"] > 0


def test_absent_si_planifie_sans_pointage(db, ref):
    e = Employe(nom="Sara", site_id=ref["site1"].id)
    db.add(e); db.flush()
    db.add(HoraireEmploye(employe_id=e.id, jour=date.today().weekday(),
                          debut=time(8, 0), fin=time(17, 0)))
    db.commit()
    l = _ligne(db, e.id)
    assert l["statut"] == "absent"


def test_non_planifie(db, ref):
    e = Employe(nom="Nabil", site_id=ref["site1"].id)
    db.add(e); db.commit()
    l = _ligne(db, e.id)
    assert l["statut"] == "non_planifie"
