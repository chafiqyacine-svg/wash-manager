"""Tests de l'export comptable CSV (recettes, clôtures) + permissions."""
from datetime import date, datetime, timezone

from app.core.security import hash_password
from app.models import Ticket, Utilisateur
from app.services.cloture import enregistrer_cloture


def test_export_recettes_csv(client, db, ref):
    db.add_all([
        Ticket(forfait_id=ref["premium"].id, prix=60, mode_paiement="espece",
               plaque="12345-A-67", site_id=ref["site1"].id, statut="ouvert",
               heure=datetime.now(timezone.utc)),
        Ticket(forfait_id=ref["rapide"].id, prix=30, mode_paiement="carte",
               site_id=ref["site1"].id, statut="annule",   # exclu
               heure=datetime.now(timezone.utc)),
    ])
    db.commit()
    r = client.get("/api/v1/export/recettes.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    lignes = r.text.strip().splitlines()
    assert lignes[0].endswith("Date;Forfait;Prix;Mode;Plaque;Statut;Site")
    corps = "\n".join(lignes[1:])
    assert "12345-A-67" in corps and "60.00" in corps
    assert "annule" not in corps          # ticket annulé exclu


def test_export_clotures_csv(client, db, ref):
    enregistrer_cloture(db, date.today(), ref["site1"].id, montant_compte=60, fond_caisse=0)
    r = client.get("/api/v1/export/clotures.csv")
    assert r.status_code == 200
    lignes = r.text.strip().splitlines()
    assert "Jour;Site;Tickets;Total;Fond;Compté;Écart" in lignes[0]
    assert len(lignes) >= 2


def test_export_reserve_admin_manager(client, db, ref):
    db.add(Utilisateur(email="c@t", nom="C", hashed_password=hash_password("pw"),
                       role="caissier", site_id=ref["site1"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login",
                      data={"username": "c@t", "password": "pw"}).json()["access_token"]
    r = client.get("/api/v1/export/recettes.csv", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
