"""Horaires : ouverture des sites et créneaux de travail des employés.

Le PUT remplace l'intégralité de la semaine (plus simple pour un éditeur
d'horaires hebdomadaire).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Employe, HoraireEmploye, HoraireSite, Site
from app.schemas.horaire import HoraireEmployeItem, HoraireSiteItem

router = APIRouter(tags=["horaires"], dependencies=[Depends(get_current_user)])


# ─── Horaires d'ouverture d'un site ──────────────────────────────────────────
@router.get("/sites/{site_id}/horaires", response_model=list[HoraireSiteItem])
def horaires_site(site_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(HoraireSite).where(HoraireSite.site_id == site_id).order_by(HoraireSite.jour)
    ).all()


@router.put("/sites/{site_id}/horaires", response_model=list[HoraireSiteItem])
def maj_horaires_site(site_id: int, horaires: list[HoraireSiteItem], db: Session = Depends(get_db)):
    if db.get(Site, site_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site inconnu")
    db.execute(delete(HoraireSite).where(HoraireSite.site_id == site_id))
    for h in horaires:
        db.add(HoraireSite(site_id=site_id, jour=h.jour,
                           heure_ouverture=h.heure_ouverture,
                           heure_fermeture=h.heure_fermeture))
    db.commit()
    return horaires_site(site_id, db)


# ─── Horaires de travail d'un employé ────────────────────────────────────────
@router.get("/employes/{employe_id}/horaires", response_model=list[HoraireEmployeItem])
def horaires_employe(employe_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(HoraireEmploye).where(HoraireEmploye.employe_id == employe_id)
        .order_by(HoraireEmploye.jour, HoraireEmploye.debut)
    ).all()


@router.put("/employes/{employe_id}/horaires", response_model=list[HoraireEmployeItem])
def maj_horaires_employe(employe_id: int, horaires: list[HoraireEmployeItem], db: Session = Depends(get_db)):
    if db.get(Employe, employe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employé inconnu")
    db.execute(delete(HoraireEmploye).where(HoraireEmploye.employe_id == employe_id))
    for h in horaires:
        db.add(HoraireEmploye(employe_id=employe_id, jour=h.jour, debut=h.debut, fin=h.fin))
    db.commit()
    return horaires_employe(employe_id, db)
