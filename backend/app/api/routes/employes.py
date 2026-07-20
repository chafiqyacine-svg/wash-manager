"""Gestion des employés et de leurs métriques de performance (cf. section 8)."""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.core.database import get_db
from app.models import Employe, Forfait, Transaction
from app.schemas.common import EmployeCreate, EmployeOut, EmployeUpdate
from app.services.presence import presence_du_jour
from app.services.rapport import _perf_employes

router = APIRouter(prefix="/employes", tags=["employes"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[EmployeOut])
def lister_employes(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site)):
    stmt = select(Employe)
    if site_id:
        stmt = stmt.where(Employe.site_id == site_id)
    return db.scalars(stmt).all()


@router.post("", response_model=EmployeOut, status_code=status.HTTP_201_CREATED)
def creer_employe(payload: EmployeCreate, db: Session = Depends(get_db)) -> Employe:
    employe = Employe(**payload.model_dump())
    db.add(employe)
    db.commit()
    db.refresh(employe)
    return employe


@router.patch("/{employe_id}", response_model=EmployeOut)
def modifier_employe(employe_id: int, payload: EmployeUpdate, db: Session = Depends(get_db)) -> Employe:
    employe = db.get(Employe, employe_id)
    if employe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employé inconnu")
    for champ, valeur in payload.model_dump(exclude_none=True).items():
        setattr(employe, champ, valeur)
    db.commit()
    db.refresh(employe)
    return employe


@router.get("/performance")
def performance(
    db: Session = Depends(get_db),
    jours: int = 7,
    site_id: int | None = Depends(resolve_site),
) -> list[dict]:
    """Classement des employés sur une période (véhicules, temps moyen, taux de
    conformité, revenus, score qualité), trié par score décroissant."""
    debut = datetime.combine(date.today() - timedelta(days=jours - 1), time.min)

    # Employés concernés (affectés au site si filtré).
    emp_stmt = select(Employe)
    if site_id:
        emp_stmt = emp_stmt.where(Employe.site_id == site_id)
    employes = db.scalars(emp_stmt).all()
    emp_ids = [e.id for e in employes]

    stmt = select(Transaction).where(
        Transaction.statut == "cloturee",
        Transaction.heure_sortie >= debut,
        Transaction.employe_id.in_(emp_ids) if emp_ids else Transaction.employe_id.is_(None),
    )
    txns = db.scalars(stmt).all()

    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}
    noms = {e.id: e.nom for e in employes}
    return _perf_employes(txns, prix, noms)


@router.get("/presence")
def presence(db: Session = Depends(get_db), jour: date | None = None,
             site_id: int | None = Depends(resolve_site)) -> list[dict]:
    """Présence, ponctualité et productivité des employés pour un jour donné."""
    return presence_du_jour(db, jour or date.today(), site_id)


@router.get("/{employe_id}/metriques")
def metriques_employe(employe_id: int, db: Session = Depends(get_db)) -> dict:
    """Métriques d'un employé : véhicules/jour, temps moyen, taux conformité,
    temps mort, revenus générés, score qualité (cf. tableau 8.2).

    TODO(dev): calculer sur une période donnée (query params debut/fin).
    """
    return {
        "employe_id": employe_id,
        "vehicules_jour": 0,
        "temps_moyen_min": 0.0,
        "taux_conformite": 0.0,
        "temps_mort_min": 0.0,
        "revenus_generes": 0.0,
        "score_qualite": 0.0,
    }
