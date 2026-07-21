"""Calcul de la marge par forfait.

Réutilise la recette de consommation (`ForfaitProduit`) et le coût d'achat
unitaire de chaque produit (`Produit.prix_unitaire`) :

    coût produits d'un lavage = Σ  prix_unitaire(produit) / lavages_par_unite
                              recette
    marge                     = prix du forfait − coût produits
    taux de marge (%)         = marge / prix × 100

Les produits étant rattachés à un site, le coût — et donc la marge — se
calcule **par site** : le même forfait peut coûter plus cher là où les
consommables sont plus onéreux. Filtrer par `site_id` restreint la recette
aux produits de ce site.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Forfait, ForfaitProduit


def _cout_produits(db: Session, forfait_id: int, site_id: int | None) -> tuple[float, list[dict]]:
    """Coût des consommables pour un lavage + le détail ligne par ligne."""
    lignes = db.scalars(
        select(ForfaitProduit).where(ForfaitProduit.forfait_id == forfait_id)
    ).all()
    cout = 0.0
    detail: list[dict] = []
    for fp in lignes:
        produit = fp.produit
        if produit is None or not produit.actif:
            continue
        if site_id and produit.site_id != site_id:
            continue
        par_unite = max(1, fp.lavages_par_unite)
        cout_ligne = float(produit.prix_unitaire) / par_unite
        cout += cout_ligne
        detail.append({
            "produit_id": produit.id,
            "produit": produit.nom,
            "unite": produit.unite,
            "prix_unitaire": float(produit.prix_unitaire),
            "lavages_par_unite": par_unite,
            "cout_par_lavage": round(cout_ligne, 4),
        })
    return round(cout, 4), detail


def marge_forfait(db: Session, forfait: Forfait, site_id: int | None = None) -> dict:
    """Renvoie prix, coût produits, marge et taux de marge pour un forfait."""
    cout, detail = _cout_produits(db, forfait.id, site_id)
    prix = float(forfait.prix)
    marge = round(prix - cout, 4)
    taux = round(marge / prix * 100, 1) if prix else None
    return {
        "forfait_id": forfait.id,
        "forfait": forfait.nom,
        "prix": prix,
        "cout_produits": cout,
        "marge": marge,
        "taux_marge": taux,
        "detail": detail,
    }


def marges(db: Session, site_id: int | None = None) -> list[dict]:
    """Marge de tous les forfaits (optionnellement pour un site donné)."""
    forfaits = db.scalars(select(Forfait).order_by(Forfait.prix)).all()
    return [marge_forfait(db, f, site_id) for f in forfaits]
