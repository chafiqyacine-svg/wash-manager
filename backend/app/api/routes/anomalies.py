"""Consultation et résolution des anomalies (avec emplacement)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Anomalie, Bay, Employe, Site, Transaction, Utilisateur
from app.schemas.common import AnomalieOut
from app.services.audit import journaliser

router = APIRouter(prefix="/anomalies", tags=["anomalies"],
                   dependencies=[Depends(get_current_user)])


def _emplacement(db: Session, a: Anomalie) -> tuple[int | None, str | None, str | None]:
    """Résout (site_id, nom du site, plaque) d'une anomalie via sa transaction
    (baie → site) ou son employé (site d'affectation)."""
    if a.transaction_id:
        txn = db.get(Transaction, a.transaction_id)
        if txn is not None:
            plaque = txn.vehicule.plaque if txn.vehicule else None
            if txn.bay_id:
                bay = db.get(Bay, txn.bay_id)
                if bay:
                    site = db.get(Site, bay.site_id)
                    return bay.site_id, site.nom if site else None, plaque
            return None, None, plaque
    if a.employe_id:
        emp = db.get(Employe, a.employe_id)
        if emp and emp.site_id:
            site = db.get(Site, emp.site_id)
            return emp.site_id, site.nom if site else None, None
    return None, None, None


@router.get("")
def lister_anomalies(db: Session = Depends(get_db), resolu: bool | None = None,
                     site_id: int | None = Depends(resolve_site)) -> list[dict]:
    stmt = select(Anomalie).order_by(Anomalie.heure.desc())
    if resolu is not None:
        stmt = stmt.where(Anomalie.resolu == resolu)
    anomalies = db.scalars(stmt).all()

    lignes = []
    for a in anomalies:
        s_id, s_nom, plaque = _emplacement(db, a)
        # Sécurité multi-site : un utilisateur rattaché ne voit que son site.
        if site_id is not None and s_id is not None and s_id != site_id:
            continue
        lignes.append({
            "id": a.id, "type": a.type, "severite": a.severite,
            "description": a.description, "heure": a.heure,
            "photo": a.photo, "notifie": a.notifie, "resolu": a.resolu,
            "transaction_id": a.transaction_id, "employe_id": a.employe_id,
            "site_id": s_id, "site": s_nom, "vehicule": plaque,
        })
    return lignes


@router.post("/{anomalie_id}/resoudre", response_model=AnomalieOut)
def resoudre_anomalie(anomalie_id: int, db: Session = Depends(get_db),
                      user: Utilisateur = Depends(get_current_user)):
    anomalie = db.get(Anomalie, anomalie_id)
    if anomalie is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Anomalie inconnue")
    anomalie.resolu = True
    db.commit()
    s_id, _, _ = _emplacement(db, anomalie)
    journaliser(db, user, "anomalie.resoudre", cible="anomalie", cible_id=anomalie.id,
                site_id=s_id, details={"type": anomalie.type})
    live_manager.notifier({"type": "update", "source": "anomalie"})
    return anomalie
