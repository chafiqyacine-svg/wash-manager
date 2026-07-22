"""Export comptable (CSV) : recettes (tickets) et clôtures de caisse.

CSV compatible Excel FR (séparateur « ; » + BOM UTF-8). Réservé admin/manager,
cloisonné par site.
"""
import csv
import io
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role, resolve_site
from app.core.database import get_db
from app.models import ClotureCaisse, Forfait, Site, Ticket, Utilisateur

router = APIRouter(prefix="/export", tags=["export"],
                   dependencies=[Depends(require_role("admin", "manager"))])


def _csv(nom: str, entetes: list[str], lignes: list[list]) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(entetes)
    w.writerows(lignes)
    # BOM UTF-8 pour qu'Excel affiche correctement les accents.
    contenu = "﻿" + buf.getvalue()
    return Response(content=contenu, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nom}"'})


def _bornes(debut: date | None, fin: date | None) -> tuple[datetime, datetime]:
    """Fenêtre [debut 00:00, fin+1j) ; défaut = les 30 derniers jours."""
    fin = fin or date.today()
    debut = debut or (fin - timedelta(days=30))
    return datetime.combine(debut, time.min), datetime.combine(fin, time.min) + timedelta(days=1)


@router.get("/recettes.csv")
def recettes(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site),
             debut: date | None = None, fin: date | None = None) -> Response:
    """Tickets encaissés (hors annulés) sur la période, une ligne par ticket."""
    d0, d1 = _bornes(debut, fin)
    stmt = select(Ticket).where(Ticket.statut != "annule",
                                Ticket.heure >= d0, Ticket.heure < d1).order_by(Ticket.heure)
    if site_id:
        stmt = stmt.where(Ticket.site_id == site_id)
    tickets = db.scalars(stmt).all()

    noms_forfait = {f.id: f.nom for f in db.scalars(select(Forfait)).all()}
    noms_site = {s.id: s.nom for s in db.scalars(select(Site)).all()}
    lignes = [[
        t.heure.isoformat(sep=" ", timespec="minutes") if t.heure else "",
        noms_forfait.get(t.forfait_id, ""),
        f"{float(t.prix):.2f}",
        t.mode_paiement,
        t.plaque or "",
        t.statut,
        noms_site.get(t.site_id, "") if t.site_id else "",
    ] for t in tickets]
    return _csv("recettes.csv",
                ["Date", "Forfait", "Prix", "Mode", "Plaque", "Statut", "Site"], lignes)


@router.get("/clotures.csv")
def clotures(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site),
             debut: date | None = None, fin: date | None = None) -> Response:
    """Clôtures de caisse (rapports Z) de la période."""
    fin = fin or date.today()
    debut = debut or (fin - timedelta(days=30))
    stmt = select(ClotureCaisse).where(ClotureCaisse.jour >= debut, ClotureCaisse.jour <= fin
                                       ).order_by(ClotureCaisse.jour)
    if site_id:
        stmt = stmt.where(ClotureCaisse.site_id == site_id)
    clots = db.scalars(stmt).all()

    noms_site = {s.id: s.nom for s in db.scalars(select(Site)).all()}
    lignes = [[
        c.jour.isoformat(),
        noms_site.get(c.site_id, "") if c.site_id else "Tous",
        str(c.nb_tickets),
        f"{float(c.total_theorique):.2f}",
        f"{float(c.fond_caisse):.2f}",
        f"{float(c.montant_compte):.2f}",
        f"{float(c.ecart):.2f}",
    ] for c in clots]
    return _csv("clotures.csv",
                ["Jour", "Site", "Tickets", "Total", "Fond", "Compté", "Écart"], lignes)
