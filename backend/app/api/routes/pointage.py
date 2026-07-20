"""Pointage des employés (arrivée/départ) avec selfie horodaté par le serveur.

Le selfie est capturé en direct côté navigateur (caméra) puis envoyé ici ;
le serveur enregistre l'heure exacte de réception — non falsifiable par le client.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Employe, Pointage
from app.services.alertes import verifier_retard
from app.services.photo import enregistrer_selfie

router = APIRouter(prefix="/pointage", tags=["pointage"],
                   dependencies=[Depends(get_current_user)])


@router.post("", status_code=status.HTTP_201_CREATED)
async def pointer(
    employe_id: int = Form(...),
    type: str = Form("arrivee"),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    employe = db.get(Employe, employe_id)
    if employe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employé inconnu")

    # Heure serveur = autoritaire (empêche l'antidatage avec une vieille photo).
    heure = datetime.now(timezone.utc)
    contenu = await selfie.read()
    chemin = enregistrer_selfie(contenu, settings.media_root, employe_id, heure)

    pointage = Pointage(employe_id=employe_id, type=type, heure=heure, photo=chemin)
    db.add(pointage)
    db.commit()
    db.refresh(pointage)

    # Alerte de retard à l'arrivée (au-delà de la tolérance configurée).
    retard = None
    if type == "arrivee":
        alerte = verifier_retard(db, employe_id, heure)
        retard = alerte.description if alerte else None

    return {
        "id": pointage.id,
        "employe_id": employe_id,
        "type": type,
        "heure": heure,
        "photo_url": f"{settings.media_base_url}/{chemin}",
        "alerte_retard": retard,
    }


@router.get("")
def liste_pointages(db: Session = Depends(get_db), limit: int = 30) -> list[dict]:
    lignes = db.scalars(
        select(Pointage).order_by(Pointage.heure.desc()).limit(limit)
    ).all()
    return [
        {
            "id": p.id,
            "employe": p.employe.nom if p.employe else None,
            "type": p.type,
            "heure": p.heure,
            "photo_url": f"{settings.media_base_url}/{p.photo}" if p.photo else None,
        }
        for p in lignes
    ]
