"""Tests du calcul de marge par forfait (coût consommables + rentabilité)."""
from app.models import ForfaitProduit, Produit
from app.services.marge import marge_forfait, marges


def _recette(db, ref):
    """Premium (prix 60) consomme : cire 40 DH/L tous les 4 lavages,
    shampoing 20 DH/L tous les 2 lavages → coût = 10 + 10 = 20 → marge 40."""
    cire = Produit(site_id=ref["site1"].id, nom="Cire", unite="L",
                   quantite=10, prix_unitaire=40)
    shp = Produit(site_id=ref["site1"].id, nom="Shampoing", unite="L",
                  quantite=10, prix_unitaire=20)
    db.add_all([cire, shp]); db.flush()
    db.add(ForfaitProduit(forfait_id=ref["premium"].id, produit_id=cire.id, lavages_par_unite=4))
    db.add(ForfaitProduit(forfait_id=ref["premium"].id, produit_id=shp.id, lavages_par_unite=2))
    db.commit()
    return cire, shp


def test_marge_calcul(db, ref):
    _recette(db, ref)
    m = marge_forfait(db, ref["premium"], site_id=ref["site1"].id)
    assert m["cout_produits"] == 20.0
    assert m["marge"] == 40.0
    assert m["taux_marge"] == round(40 / 60 * 100, 1)
    assert len(m["detail"]) == 2


def test_marge_sans_recette_egale_prix(db, ref):
    m = marge_forfait(db, ref["rapide"])
    assert m["cout_produits"] == 0.0
    assert m["marge"] == float(ref["rapide"].prix)


def test_marge_filtre_par_site(db, ref):
    _recette(db, ref)  # produits sur site1
    # Sur site2 : aucun produit de la recette → coût 0.
    m = marge_forfait(db, ref["premium"], site_id=ref["site2"].id)
    assert m["cout_produits"] == 0.0
    assert m["detail"] == []


def test_marges_liste_tous_forfaits(db, ref):
    _recette(db, ref)
    res = marges(db, site_id=ref["site1"].id)
    assert {m["forfait"] for m in res} == {"Rapide", "Premium", "Complet"}


def test_api_marges(client, ref):
    r = client.get("/api/v1/marges")
    assert r.status_code == 200
    assert any(m["forfait"] == "Premium" for m in r.json())
