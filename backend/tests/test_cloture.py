"""Tests de la clôture de caisse (rapport Z) : agrégation, écart, API, multi-site."""
from datetime import date, datetime, timezone

from app.models import ClotureCaisse, Ticket
from app.services.cloture import calculer_cloture, enregistrer_cloture


def _ticket(db, ref, prix, mode="espece", site=None, statut="ouvert"):
    t = Ticket(forfait_id=ref["premium"].id, prix=prix, mode_paiement=mode,
               site_id=site, statut=statut, heure=datetime.now(timezone.utc))
    db.add(t); db.flush()
    return t


def test_calcul_ventile_par_mode(db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    _ticket(db, ref, 40, "espece", ref["site1"].id)
    _ticket(db, ref, 100, "carte", ref["site1"].id)
    _ticket(db, ref, 30, "espece", ref["site1"].id, statut="annule")  # ignoré
    db.commit()
    ap = calculer_cloture(db, date.today(), ref["site1"].id)
    assert ap["nb_tickets"] == 3
    assert ap["total_theorique"] == 200.0
    assert ap["total_especes"] == 100.0
    assert ap["detail_modes"]["espece"]["nb"] == 2
    assert ap["detail_modes"]["carte"]["total"] == 100.0
    assert ap["deja_cloturee"] is False


def test_ecart_de_caisse(db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    _ticket(db, ref, 40, "carte", ref["site1"].id)
    db.commit()
    # Espèces théoriques = 60, fond = 100 → attendu 160 ; compté 158 → écart -2.
    c = enregistrer_cloture(db, date.today(), ref["site1"].id,
                            montant_compte=158, fond_caisse=100, notes="test")
    assert c.id is not None
    assert float(c.ecart) == -2.0
    assert float(c.total_theorique) == 100.0
    assert c.fichier_pdf and c.fichier_pdf.endswith(".pdf")


def test_cloture_isolee_par_site(db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    _ticket(db, ref, 90, "espece", ref["site2"].id)
    db.commit()
    ap1 = calculer_cloture(db, date.today(), ref["site1"].id)
    ap2 = calculer_cloture(db, date.today(), ref["site2"].id)
    assert ap1["total_theorique"] == 60.0
    assert ap2["total_theorique"] == 90.0


def test_api_apercu_puis_cloture(client, db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    db.commit()
    jour = date.today().isoformat()
    r = client.get(f"/api/v1/cloture/apercu?jour={jour}&site_id={ref['site1'].id}")
    assert r.status_code == 200 and r.json()["total_especes"] == 60.0

    r2 = client.post("/api/v1/cloture", json={
        "jour": jour, "site_id": ref["site1"].id,
        "montant_compte": 60, "fond_caisse": 0,
    })
    assert r2.status_code == 201
    assert r2.json()["ecart"] == 0.0

    # Deuxième clôture du même jour/site refusée.
    r3 = client.post("/api/v1/cloture", json={
        "jour": jour, "site_id": ref["site1"].id, "montant_compte": 60,
    })
    assert r3.status_code == 409


def test_api_historique(client, db, ref):
    enregistrer_cloture(db, date.today(), ref["site1"].id, montant_compte=0)
    r = client.get("/api/v1/cloture")
    assert r.status_code == 200
    assert len(r.json()) >= 1
