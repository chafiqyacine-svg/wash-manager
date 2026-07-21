"""Clôture de caisse journalière (rapport Z) : aperçu, clôture, historique, PDF."""
import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role, resolve_site
from app.core.config import settings
from app.core.database import get_db
from app.models import ClotureCaisse, Utilisateur
from app.services.cloture import calculer_cloture, enregistrer_cloture

router = APIRouter(prefix="/cloture", tags=["cloture"],
                   dependencies=[Depends(get_current_user)])


class ClotureIn(BaseModel):
    jour: date
    site_id: int | None = None
    montant_compte: float = 0
    fond_caisse: float = 0
    notes: str | None = None


class ClotureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int | None
    jour: date
    nb_tickets: int
    total_theorique: float
    detail_modes: dict
    fond_caisse: float
    montant_compte: float
    ecart: float
    notes: str | None
    fichier_pdf: str | None


@router.get("/apercu")
def apercu(jour: date, db: Session = Depends(get_db),
           site_id: int | None = Depends(resolve_site)):
    """Totaux théoriques du jour (par mode de paiement) avant clôture."""
    return calculer_cloture(db, jour, site_id)


@router.get("", response_model=list[ClotureOut])
def historique(db: Session = Depends(get_db),
               site_id: int | None = Depends(resolve_site)):
    stmt = select(ClotureCaisse).order_by(ClotureCaisse.jour.desc())
    if site_id:
        stmt = stmt.where(ClotureCaisse.site_id == site_id)
    return db.scalars(stmt).all()


@router.post("", response_model=ClotureOut, status_code=status.HTTP_201_CREATED)
def cloturer(payload: ClotureIn, db: Session = Depends(get_db),
             user: Utilisateur = Depends(require_role("admin", "manager"))):
    """Fige la clôture du jour (une seule par jour/site) et calcule l'écart."""
    # Sécurité multi-site : un manager rattaché est forcé sur son site.
    site_id = user.site_id if (user.role != "admin" and user.site_id) else payload.site_id
    apercu_data = calculer_cloture(db, payload.jour, site_id)
    if apercu_data["deja_cloturee"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Caisse déjà clôturée pour ce jour/site")
    return enregistrer_cloture(
        db, payload.jour, site_id,
        montant_compte=payload.montant_compte, fond_caisse=payload.fond_caisse,
        notes=payload.notes, user_id=user.id,
    )


@router.get("/{cloture_id}/pdf")
def telecharger_pdf(cloture_id: int, db: Session = Depends(get_db)):
    cloture = db.get(ClotureCaisse, cloture_id)
    if cloture is None or not cloture.fichier_pdf:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clôture ou PDF introuvable")
    chemin = os.path.join(settings.media_root, cloture.fichier_pdf)
    if not os.path.exists(chemin):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fichier PDF absent du stockage")
    return FileResponse(chemin, media_type="application/pdf",
                        filename=os.path.basename(chemin))
