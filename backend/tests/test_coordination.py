"""Test de coordination bout-en-bout des nouvelles fonctionnalités.

Vérifie que les briques s'enchaînent correctement :
  caisse (mode paiement + site) → clôture de caisse (écart, par mode)
  inventaire (prix unitaire) + recette → marge par forfait
et que la sécurité multi-site est respectée de bout en bout.
"""
from datetime import date

from app.core.security import hash_password
from app.models import ForfaitProduit, Produit, Utilisateur


def test_caisse_vers_cloture(client, ref):
    """Encaisser 2 tickets (espèce + carte) puis clôturer → écart cohérent."""
    # Encaissements via la caisse (l'admin fournit le site explicitement).
    for mode in ("espece", "carte"):
        r = client.post("/api/v1/tickets", json={
            "forfait_id": ref["premium"].id, "mode_paiement": mode,
            "site_id": ref["site1"].id,
        })
        assert r.status_code == 201
        assert r.json()["mode_paiement"] == mode
        assert r.json()["site_id"] == ref["site1"].id

    jour = date.today().isoformat()
    ap = client.get(f"/api/v1/cloture/apercu?jour={jour}&site_id={ref['site1'].id}").json()
    assert ap["nb_tickets"] == 2
    assert ap["total_theorique"] == 120.0
    assert ap["total_especes"] == 60.0  # seule l'espèce compte pour le tiroir

    # Clôture : fond 100 + espèces 60 = 160 attendu ; compté 160 → écart 0.
    r = client.post("/api/v1/cloture", json={
        "jour": jour, "site_id": ref["site1"].id,
        "montant_compte": 160, "fond_caisse": 100,
    })
    assert r.status_code == 201
    c = r.json()
    assert c["ecart"] == 0.0
    assert c["detail_modes"]["carte"]["total"] == 60.0
    assert c["fichier_pdf"]

    # Le PDF est réellement servi.
    pdf = client.get(f"/api/v1/cloture/{c['id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"


def test_inventaire_vers_marge(client, db, ref):
    """Prix unitaire produit + recette → marge calculée et exposée par l'API."""
    r = client.post("/api/v1/produits", json={
        "nom": "Cire", "unite": "L", "quantite": 10,
        "prix_unitaire": 40, "site_id": ref["site1"].id,
    })
    assert r.status_code == 201 and r.json()["prix_unitaire"] == 40.0
    produit_id = r.json()["id"]

    # Recette : 1 L de cire tous les 4 lavages Premium → coût 10 → marge 50.
    r = client.put(f"/api/v1/forfaits/{ref['premium'].id}/consommation",
                   json=[{"produit_id": produit_id, "lavages_par_unite": 4}])
    assert r.status_code == 200

    marges = client.get(f"/api/v1/marges?site_id={ref['site1'].id}").json()
    prem = next(m for m in marges if m["forfait"] == "Premium")
    assert prem["cout_produits"] == 10.0
    assert prem["marge"] == 50.0


def test_cloture_securite_multisite(client, db, ref):
    """Un manager du site 2 ne peut pas clôturer le site 1 : forcé sur son site."""
    db.add(Utilisateur(email="mgr2@test", nom="M2", hashed_password=hash_password("pw"),
                       role="manager", site_id=ref["site2"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login",
                      data={"username": "mgr2@test", "password": "pw"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Ticket encaissé côté site 1 (par l'admin).
    client.post("/api/v1/tickets", json={
        "forfait_id": ref["premium"].id, "mode_paiement": "espece", "site_id": ref["site1"].id})

    jour = date.today().isoformat()
    # Le manager demande le site 1 mais est forcé sur le site 2 (vide) → 0.
    r = client.post("/api/v1/cloture", json={
        "jour": jour, "site_id": ref["site1"].id, "montant_compte": 0}, headers=h)
    assert r.status_code == 201
    assert r.json()["site_id"] == ref["site2"].id
    assert r.json()["total_theorique"] == 0.0


def test_caissier_ticket_force_sur_son_site(client, db, ref):
    """Un caissier du site 2 encaisse : le ticket est rattaché à son site, pas au site demandé."""
    db.add(Utilisateur(email="caisse@test", nom="C", hashed_password=hash_password("pw"),
                       role="caissier", site_id=ref["site2"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login",
                      data={"username": "caisse@test", "password": "pw"}).json()["access_token"]
    r = client.post("/api/v1/tickets", json={
        "forfait_id": ref["rapide"].id, "site_id": ref["site1"].id},  # tente site 1
        headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 201
    assert r.json()["site_id"] == ref["site2"].id  # forcé sur le site du caissier
