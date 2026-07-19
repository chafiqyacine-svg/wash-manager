"""Accès aux paramètres configurables (avec valeurs par défaut).

Les clés connues et leurs défauts sont centralisés ici pour éviter les valeurs
magiques dispersées dans le code.
"""
from sqlalchemy.orm import Session

from app.models import Parametre

# Clé -> (valeur par défaut, description)
DEFAUTS: dict[str, tuple[str, str]] = {
    "fenetre_rapprochement_minutes": (
        "30", "Fenêtre (minutes) de rapprochement automatique ticket ↔ véhicule."
    ),
}


def get_param(db: Session, cle: str) -> str:
    p = db.get(Parametre, cle)
    if p is not None:
        return p.valeur
    return DEFAUTS.get(cle, ("", ""))[0]


def get_int(db: Session, cle: str, defaut: int = 0) -> int:
    try:
        return int(get_param(db, cle) or defaut)
    except (TypeError, ValueError):
        return defaut


def set_param(db: Session, cle: str, valeur: str) -> Parametre:
    p = db.get(Parametre, cle)
    if p is None:
        p = Parametre(cle=cle, valeur=valeur, description=DEFAUTS.get(cle, ("", ""))[1])
        db.add(p)
    else:
        p.valeur = valeur
    db.commit()
    db.refresh(p)
    return p


def lister_params(db: Session) -> dict[str, str]:
    """Tous les paramètres (défauts + surcharges en base)."""
    valeurs = {cle: defaut for cle, (defaut, _) in DEFAUTS.items()}
    for p in db.query(Parametre).all():
        valeurs[p.cle] = p.valeur
    return valeurs
