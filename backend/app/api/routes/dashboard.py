"""KPI agrégés pour le dashboard (vue temps réel + chiffres du jour)."""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Anomalie, Forfait, Transaction
from app.models.enums import ZoneCode

router = APIRouter(prefix="/dashboard", tags=["dashboard"],
                   dependencies=[Depends(get_current_user)])


@router.get("/kpi")
def kpi_du_jour(db: Session = Depends(get_db)) -> dict:
    """KPI du jour : nb véhicules, CA, temps moyen, taux de conformité."""
    debut = datetime.combine(date.today(), time.min)
    fin = debut + timedelta(days=1)

    txns = db.scalars(
        select(Transaction).where(
            Transaction.statut == "cloturee",
            Transaction.heure_sortie >= debut,
            Transaction.heure_sortie < fin,
        )
    ).all()
    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}

    ca = sum(prix.get(t.forfait_id, 0.0) for t in txns if t.forfait_id)
    durees = [t.duree_totale for t in txns if t.duree_totale]
    temps_moyen = round(sum(durees) / len(durees) / 60, 1) if durees else 0.0
    evaluees = [t for t in txns if t.conforme is not None]
    conformes = sum(1 for t in evaluees if t.conforme)
    taux = round(conformes / len(evaluees) * 100, 1) if evaluees else 0.0

    anomalies_ouvertes = db.query(Anomalie).filter(Anomalie.resolu.is_(False)).count()

    return {
        "vehicules": len(txns),
        "chiffre_affaires": round(ca, 2),
        "temps_moyen_min": temps_moyen,
        "taux_conformite": taux,
        "anomalies_ouvertes": anomalies_ouvertes,
    }


# Colonnes de début de zone -> code zone (pour déduire la position courante).
_ZONE_DEBUTS = [
    ("zone_d_debut", ZoneCode.POLISH.value),
    ("zone_c_debut", ZoneCode.ASPIRATION.value),
    ("zone_b_debut", ZoneCode.LAVAGE_EXT.value),
]


@router.get("/en-cours")
def vehicules_en_cours(db: Session = Depends(get_db)) -> list[dict]:
    """Véhicules actuellement sur le site (transactions statut=en_cours)."""
    txns = db.scalars(
        select(Transaction).where(Transaction.statut == "en_cours")
        .order_by(Transaction.heure_entree)
    ).all()

    resultat = []
    for t in txns:
        # Zone courante = la zone la plus avancée dont le début est renseigné.
        zone = next((code for champ, code in _ZONE_DEBUTS if getattr(t, champ)), ZoneCode.ENTREE.value)
        resultat.append({
            "transaction_id": t.id,
            "track_id": t.track_id,
            "plaque": t.vehicule.plaque if t.vehicule else None,
            "heure_entree": t.heure_entree,
            "zone_courante": zone,
        })
    return resultat
