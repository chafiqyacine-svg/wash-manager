"""Tâches de maintenance des données.

Nettoyage des transactions « orphelines » : un véhicule détecté à l'entrée mais
jamais vu en sortie (perte de suivi caméra, véhicule reparti sans franchir la
ligne…) laisse une transaction bloquée en « en_cours », ce qui gonfle
indéfiniment le compteur des lavages en cours. On les clôture automatiquement
avec le statut « abandonnee » (exclu des KPI terminés ET des en-cours).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction
from app.services.parametres import get_int


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def nettoyer_transactions_orphelines(db: Session, maintenant: datetime | None = None) -> int:
    """Clôture (statut « abandonnee ») les lavages en cours trop anciens.
    Retourne le nombre de transactions traitées."""
    maintenant = _aware(maintenant or datetime.now(timezone.utc))
    seuil = maintenant - timedelta(hours=get_int(db, "delai_abandon_heures", 4))

    en_cours = db.scalars(
        select(Transaction).where(Transaction.statut == "en_cours")
    ).all()

    n = 0
    for txn in en_cours:
        if txn.heure_entree is None:
            continue
        if _aware(txn.heure_entree) < seuil:
            txn.statut = "abandonnee"
            txn.heure_sortie = txn.heure_sortie or maintenant
            n += 1
    if n:
        db.commit()
    return n
