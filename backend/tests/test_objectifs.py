"""Tests des objectifs de pilotage : évaluation, écarts, API, multi-site."""
from datetime import date, datetime, timezone

from app.models import Objectif, Ticket, Transaction
from app.services.objectifs import evaluer


def _txn(db, ref, forfait_id=None, conforme=None, bay=None):
    t = Transaction(statut="cloturee", forfait_id=forfait_id, conforme=conforme,
                    bay_id=bay, heure_entree=datetime.now(timezone.utc),
                    heure_sortie=datetime.now(timezone.utc))
    db.add(t); db.flush()
    return t


def test_objectif_ca_atteint_et_manque(db, ref):
    # 2 tickets = 120 DH de recette sur site1.
    for _ in range(2):
        db.add(Ticket(forfait_id=ref["premium"].id, prix=60, mode_paiement="espece",
                      site_id=ref["site1"].id, statut="ouvert",
                      heure=datetime.now(timezone.utc)))
    db.add(Objectif(site_id=ref["site1"].id, metrique="ca_journalier", cible=100, sens="min"))
    db.commit()
    (ligne,) = [l for l in evaluer(db, date.today(), ref["site1"].id)
                if l["metrique"] == "ca_journalier"]
    assert ligne["valeur"] == 120.0 and ligne["atteint"] is True
    assert ligne["ecart"] == 20.0

    # Relève la cible au-dessus du réel -> non atteint.
    db.query(Objectif).filter(Objectif.metrique == "ca_journalier").update({"cible": 200})
    db.commit()
    (ligne,) = [l for l in evaluer(db, date.today(), ref["site1"].id)
                if l["metrique"] == "ca_journalier"]
    assert ligne["atteint"] is False and ligne["ecart"] == -80.0


def test_objectif_conformite_et_non_factures(db, ref):
    _txn(db, ref, forfait_id=ref["premium"].id, conforme=True, bay=ref["bay"].id)
    _txn(db, ref, forfait_id=ref["premium"].id, conforme=False, bay=ref["bay"].id)
    _txn(db, ref, forfait_id=None, conforme=None, bay=ref["bay"].id)   # non facturé
    db.add_all([
        Objectif(site_id=ref["site1"].id, metrique="taux_conformite", cible=90, sens="min"),
        Objectif(site_id=ref["site1"].id, metrique="lavages_non_factures", cible=0, sens="max"),
    ])
    db.commit()
    res = {l["metrique"]: l for l in evaluer(db, date.today(), ref["site1"].id)}
    assert res["taux_conformite"]["valeur"] == 50.0        # 1/2 conformes
    assert res["taux_conformite"]["atteint"] is False
    assert res["lavages_non_factures"]["valeur"] == 1
    assert res["lavages_non_factures"]["atteint"] is False  # 1 > 0 (plafond dépassé)


def test_api_crud_et_evaluation(client, ref):
    # Création (upsert par site+métrique).
    r = client.post("/api/v1/objectifs", json={
        "metrique": "ca_journalier", "cible": 500, "site_id": ref["site1"].id})
    assert r.status_code == 201 and r.json()["sens"] == "min"
    oid = r.json()["id"]
    # Re-création même métrique -> met à jour (pas de doublon).
    r2 = client.post("/api/v1/objectifs", json={
        "metrique": "ca_journalier", "cible": 800, "site_id": ref["site1"].id})
    assert r2.json()["id"] == oid and r2.json()["cible"] == 800.0

    assert client.get("/api/v1/objectifs/metriques").status_code == 200
    ev = client.get(f"/api/v1/objectifs/evaluation?site_id={ref['site1'].id}")
    assert ev.status_code == 200
    assert any(l["metrique"] == "ca_journalier" for l in ev.json())

    assert client.delete(f"/api/v1/objectifs/{oid}").status_code == 204
    assert client.get(f"/api/v1/objectifs?site_id={ref['site1'].id}").json() == []


def test_metrique_inconnue_refusee(client, ref):
    r = client.post("/api/v1/objectifs", json={"metrique": "n_importe_quoi", "cible": 1})
    assert r.status_code == 422
