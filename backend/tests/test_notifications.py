"""Tests des alertes : dispatch, journalisation, déclenchement, endpoints."""
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.models import Notification, Ticket, Transaction
from app.schemas.event import EventIn, EventType
from app.services.ingestion import traiter_evenement
from app.services.notifications import notifier, notifier_anomalie


def test_notifier_journalise_meme_sans_canal(db, ref):
    # Aucun canal configuré (test) -> entrée « simule » conservée.
    entrees = notifier(db, "Sujet", "Message", severite="haute", site_id=ref["site1"].id)
    assert len(entrees) == 1
    assert entrees[0].canal == "log" and entrees[0].statut == "simule"
    assert db.scalar(select(Notification.id)) is not None


def test_notifier_anomalie_gate_par_severite(db, ref):
    assert notifier_anomalie(db, type_="x", severite="moyenne", description=None) == []
    faites = notifier_anomalie(db, type_="forfait_non_respecte", severite="critique",
                               description="Payé > effectué", site_id=ref["site1"].id)
    assert len(faites) == 1 and faites[0].severite == "critique"


def _parcours_non_conforme(db, ref):
    """Complet payé mais seulement B effectué → anomalie critique."""
    db.add(Ticket(forfait_id=ref["complet"].id, prix=100, plaque="12345-A-67",
                  heure=datetime.now(timezone.utc), statut="ouvert"))
    db.commit()
    for ev in [EventIn(type=EventType.ENTREE, track_id="c1", timestamp=datetime.now(timezone.utc)),
               EventIn(type=EventType.PLAQUE, track_id="c1", plaque="12345-A-67",
                       plaque_confiance=0.9, timestamp=datetime.now(timezone.utc)),
               EventIn(type=EventType.ZONE_ENTER, track_id="c1", zone="B",
                       timestamp=datetime.now(timezone.utc))]:
        traiter_evenement(db, ev)
    txn = db.scalar(select(Transaction).where(Transaction.track_id == "c1"))
    txn.bay_id = ref["bay"].id
    db.commit()
    traiter_evenement(db, EventIn(type=EventType.SORTIE, track_id="c1",
                                  timestamp=datetime.now(timezone.utc)))


def test_anomalie_grave_declenche_une_alerte(db, ref):
    _parcours_non_conforme(db, ref)
    alertes = db.scalars(select(Notification).where(
        Notification.ref_type == "anomalie", Notification.severite == "critique")).all()
    assert len(alertes) >= 1


def test_ecart_caisse_declenche_alerte(client, db, ref):
    db.add(Ticket(forfait_id=ref["premium"].id, prix=60, mode_paiement="espece",
                  site_id=ref["site1"].id, statut="ouvert", heure=datetime.now(timezone.utc)))
    db.commit()
    r = client.post("/api/v1/cloture", json={
        "jour": date.today().isoformat(), "site_id": ref["site1"].id,
        "montant_compte": 50, "fond_caisse": 0})   # compté 50 vs 60 -> écart -10
    assert r.status_code == 201
    alertes = db.scalars(select(Notification).where(Notification.ref_type == "cloture")).all()
    assert len(alertes) == 1 and "Écart" in alertes[0].sujet


def test_canal_configure_marque_envoye(db, ref, monkeypatch):
    """Quand un canal est configuré et l'envoi réussit, statut = envoye."""
    import app.services.notifications as N
    monkeypatch.setattr(N, "_canaux_configures", lambda: ["email"])
    monkeypatch.setattr(N, "_destinataires", lambda canal: ["boss@station.ma"])
    monkeypatch.setitem(N._EXPEDITEURS, "email", lambda d, s, m: True)
    (entree,) = N.notifier(db, "Sujet", "Message")
    assert entree.statut == "envoye"
    assert entree.canal == "email" and entree.destinataire == "boss@station.ma"


def test_canal_configure_echec_marque_echec(db, ref, monkeypatch):
    import app.services.notifications as N
    monkeypatch.setattr(N, "_canaux_configures", lambda: ["whatsapp"])
    monkeypatch.setattr(N, "_destinataires", lambda canal: ["+2126..."])
    monkeypatch.setitem(N._EXPEDITEURS, "whatsapp", lambda d, s, m: False)
    (entree,) = N.notifier(db, "S", "M")
    assert entree.statut == "echec"


def test_email_non_configure_renvoie_false():
    from app.services.notifications import _envoyer_email
    assert _envoyer_email("x@y", "s", "m") is False   # settings.smtp_host vide en test


def test_endpoints_historique_test_et_permission(client, db, ref):
    # test d'envoi (admin) -> crée une entrée
    r = client.post("/api/v1/notifications/test")
    assert r.status_code == 200 and len(r.json()) >= 1
    assert client.get("/api/v1/notifications").status_code == 200
    assert client.get("/api/v1/notifications/canaux").json()["mode"] == "simule"
