"""Tests de paiement : vue financière /payments + cas limites de clôture.

Complète test_cloture.py et test_coordination.py sur les aspects encaissement.
"""
from datetime import date, datetime, timedelta, timezone

from app.models import Ticket, Transaction
from app.services.cloture import calculer_cloture, enregistrer_cloture


def _txn(db, ref, forfait_id=None, detecte=None, bay=None):
    t = Transaction(statut="cloturee", forfait_id=forfait_id, forfait_detecte=detecte,
                    bay_id=bay, heure_entree=datetime.now(timezone.utc),
                    heure_sortie=datetime.now(timezone.utc))
    db.add(t); db.flush()
    return t


# ─── Vue /payments (payé vs en attente) ──────────────────────────────────────
def test_payments_paye_et_en_attente(client, db, ref):
    _txn(db, ref, forfait_id=ref["premium"].id, bay=ref["bay"].id)   # payé : 60
    _txn(db, ref, detecte="Rapide", bay=ref["bay"].id)               # en attente : 30
    db.commit()
    r = client.get("/api/v1/payments")
    assert r.status_code == 200
    data = r.json()
    assert data["total_paid"] == 60.0
    assert data["total_pending"] == 30.0
    assert len(data["items"]) == 2


def test_payments_filtre_par_site(client, db, ref):
    _txn(db, ref, forfait_id=ref["premium"].id, bay=ref["bay"].id)   # site1 (a une baie)
    _txn(db, ref, forfait_id=ref["complet"].id, bay=None)            # sans baie → hors site1
    db.commit()
    r = client.get(f"/api/v1/payments?site_id={ref['site1'].id}")
    data = r.json()
    assert data["total_paid"] == 60.0            # seule la transaction du site 1
    assert len(data["items"]) == 1


# ─── Clôture : cas limites ───────────────────────────────────────────────────
def _ticket(db, ref, prix, mode="espece", site=None, statut="ouvert", quand=None):
    t = Ticket(forfait_id=ref["premium"].id, prix=prix, mode_paiement=mode, site_id=site,
               statut=statut, heure=quand or datetime.now(timezone.utc))
    db.add(t); db.flush()
    return t


def test_cloture_surplus_ecart_positif(db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    db.commit()
    c = enregistrer_cloture(db, date.today(), ref["site1"].id, montant_compte=65, fond_caisse=0)
    assert float(c.ecart) == 5.0  # 5 DH de trop dans le tiroir


def test_cloture_mode_autre_hors_especes(db, ref):
    _ticket(db, ref, 100, "autre", ref["site1"].id)
    db.commit()
    ap = calculer_cloture(db, date.today(), ref["site1"].id)
    assert ap["total_theorique"] == 100.0
    assert ap["total_especes"] == 0.0            # "autre" ne compte pas comme espèces
    assert ap["detail_modes"]["autre"]["total"] == 100.0


def test_cloture_ticket_rapproche_compte(db, ref):
    """Un ticket rapproché (validé par l'IA) reste un encaissement : il compte."""
    _ticket(db, ref, 60, "espece", ref["site1"].id, statut="rapproche")
    db.commit()
    ap = calculer_cloture(db, date.today(), ref["site1"].id)
    assert ap["nb_tickets"] == 1 and ap["total_theorique"] == 60.0


def test_cloture_globale_admin_agrege_tous_sites(db, ref):
    _ticket(db, ref, 60, "espece", ref["site1"].id)
    _ticket(db, ref, 90, "espece", ref["site2"].id)
    db.commit()
    ap = calculer_cloture(db, date.today(), None)  # site_id None = tous les sites
    assert ap["total_theorique"] == 150.0


def test_cloture_isolee_par_jour(db, ref):
    hier = datetime.now(timezone.utc) - timedelta(days=1)
    _ticket(db, ref, 60, "espece", ref["site1"].id, quand=hier)      # hier
    _ticket(db, ref, 40, "espece", ref["site1"].id)                  # aujourd'hui
    db.commit()
    ap = calculer_cloture(db, date.today(), ref["site1"].id)
    assert ap["total_theorique"] == 40.0                             # hier exclu


def test_cloture_caissier_interdit(client, db, ref):
    """La clôture est réservée admin/manager : un caissier est refusé (403)."""
    from app.core.security import hash_password
    from app.models import Utilisateur
    db.add(Utilisateur(email="c@test", nom="C", hashed_password=hash_password("pw"),
                       role="caissier", site_id=ref["site1"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login",
                      data={"username": "c@test", "password": "pw"}).json()["access_token"]
    r = client.post("/api/v1/cloture",
                    json={"jour": date.today().isoformat(), "montant_compte": 0},
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
