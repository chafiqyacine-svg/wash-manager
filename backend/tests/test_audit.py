"""Tests du journal d'audit : service, endpoint, permissions, instrumentation."""
from sqlalchemy import select

from app.core.security import hash_password
from app.models import Ticket, Utilisateur
from app.services.audit import journaliser


def _login(client, email, pw):
    return client.post("/api/v1/auth/login",
                       data={"username": email, "password": pw}).json()["access_token"]


def _admin(db):
    return db.scalar(select(Utilisateur).where(Utilisateur.email == "admin@test"))


def test_service_journalise(db, ref):
    u = Utilisateur(email="a@t", nom="A", hashed_password=hash_password("x"),
                    role="admin")
    db.add(u); db.commit()
    e = journaliser(db, u, "ticket.annuler", cible="ticket", cible_id=5,
                    site_id=ref["site1"].id, details={"prix": 60})
    assert e.id is not None
    assert e.utilisateur_email == "a@t" and e.role == "admin"
    assert e.action == "ticket.annuler" and e.details["prix"] == 60


def test_endpoint_reserve_admin_manager(client, db, ref):
    # caissier -> 403
    db.add(Utilisateur(email="c@t", nom="C", hashed_password=hash_password("pw"),
                       role="caissier", site_id=ref["site1"].id))
    db.commit()
    tok = _login(client, "c@t", "pw")
    r = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_annulation_ticket_est_journalisee(client, db, ref):
    """Bout-en-bout : annuler un ticket crée une entrée d'audit consultable."""
    t = Ticket(forfait_id=ref["premium"].id, prix=60, mode_paiement="espece",
               site_id=ref["site1"].id, statut="ouvert")
    db.add(t); db.commit()
    assert client.post(f"/api/v1/tickets/{t.id}/annuler").status_code == 200

    r = client.get("/api/v1/audit")   # client = admin
    assert r.status_code == 200
    entrees = r.json()
    ann = [e for e in entrees if e["action"] == "ticket.annuler"]
    assert len(ann) == 1
    assert ann[0]["cible_id"] == t.id
    assert ann[0]["utilisateur_email"] == "admin@test"
    assert ann[0]["details"]["prix"] == 60.0


def test_filtre_par_action(client, db, ref):
    u = _admin(db)
    journaliser(db, u, "forfait.modifier", cible="forfait", cible_id=1)
    journaliser(db, u, "cloture.creer", cible="cloture", cible_id=1)
    r = client.get("/api/v1/audit?action=cloture.creer")
    actions = {e["action"] for e in r.json()}
    assert actions == {"cloture.creer"}


def test_manager_ne_voit_que_son_site(client, db, ref):
    admin = _admin(db)
    journaliser(db, admin, "stock.mouvement", cible="produit", cible_id=1,
                site_id=ref["site1"].id)
    journaliser(db, admin, "stock.mouvement", cible="produit", cible_id=2,
                site_id=ref["site2"].id)
    db.add(Utilisateur(email="m@t", nom="M", hashed_password=hash_password("pw"),
                       role="manager", site_id=ref["site1"].id))
    db.commit()
    tok = _login(client, "m@t", "pw")
    r = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {tok}"})
    sites = {e["site_id"] for e in r.json()}
    assert sites == {ref["site1"].id}
