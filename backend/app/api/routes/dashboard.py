"""KPI agrégés pour le dashboard (vue temps réel + chiffres du jour)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"],
                   dependencies=[Depends(get_current_user)])


@router.get("/kpi")
def kpi_du_jour(db: Session = Depends(get_db)) -> dict:
    """KPI du jour : nb véhicules, CA, temps moyen, taux de conformité.

    TODO(dev): implémenter les agrégations SQL (jour courant).
    """
    return {
        "vehicules": 0,
        "chiffre_affaires": 0.0,
        "temps_moyen_min": 0.0,
        "taux_conformite": 0.0,
        "anomalies_ouvertes": 0,
    }


@router.get("/en-cours")
def vehicules_en_cours(db: Session = Depends(get_db)) -> list[dict]:
    """Véhicules actuellement sur le site (transactions statut=en_cours).

    TODO(dev): retourner track_id, plaque, zone courante, chrono actif.
    """
    return []
