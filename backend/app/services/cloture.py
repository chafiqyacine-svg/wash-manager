"""Clôture de caisse journalière (rapport Z).

`calculer_cloture` agrège les tickets encaissés d'un jour/site (hors annulés),
ventilés par mode de paiement — c'est l'aperçu avant clôture.
`enregistrer_cloture` fige ces totaux, calcule l'écart de caisse à partir du
montant réellement compté par le gérant, et archive un PDF.

Écart de caisse = espèces comptées − (fond de caisse + espèces théoriques).
Les paiements par carte ne passent pas par le tiroir : ils n'entrent pas dans
le calcul de l'écart.
"""
import os
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ClotureCaisse, Site, Ticket


def calculer_cloture(db: Session, jour: date, site_id: int | None) -> dict:
    """Aperçu : totaux théoriques du jour, ventilés par mode de paiement."""
    debut = datetime.combine(jour, time.min)
    fin = debut + timedelta(days=1)

    stmt = select(Ticket).where(
        Ticket.statut != "annule",
        Ticket.heure >= debut,
        Ticket.heure < fin,
    )
    if site_id:
        stmt = stmt.where(Ticket.site_id == site_id)
    tickets = db.scalars(stmt).all()

    modes: dict[str, dict] = {}
    total = 0.0
    for t in tickets:
        montant = float(t.prix)
        total += montant
        m = modes.setdefault(t.mode_paiement or "espece", {"nb": 0, "total": 0.0})
        m["nb"] += 1
        m["total"] = round(m["total"] + montant, 2)

    return {
        "jour": jour.isoformat(),
        "site_id": site_id,
        "nb_tickets": len(tickets),
        "total_theorique": round(total, 2),
        "total_especes": round(modes.get("espece", {}).get("total", 0.0), 2),
        "detail_modes": modes,
        "deja_cloturee": _cloture_existante(db, jour, site_id) is not None,
    }


def _cloture_existante(db: Session, jour: date, site_id: int | None) -> ClotureCaisse | None:
    stmt = select(ClotureCaisse).where(ClotureCaisse.jour == jour)
    stmt = stmt.where(ClotureCaisse.site_id == site_id) if site_id \
        else stmt.where(ClotureCaisse.site_id.is_(None))
    return db.scalar(stmt)


def enregistrer_cloture(
    db: Session, jour: date, site_id: int | None,
    montant_compte: float, fond_caisse: float = 0.0,
    notes: str | None = None, user_id: int | None = None,
) -> ClotureCaisse:
    """Fige la clôture du jour et calcule l'écart de caisse. Une seule par jour/site."""
    apercu = calculer_cloture(db, jour, site_id)
    especes = apercu["total_especes"]
    ecart = round(montant_compte - (fond_caisse + especes), 2)

    cloture = ClotureCaisse(
        site_id=site_id,
        jour=jour,
        nb_tickets=apercu["nb_tickets"],
        total_theorique=apercu["total_theorique"],
        detail_modes=apercu["detail_modes"],
        fond_caisse=fond_caisse,
        montant_compte=montant_compte,
        ecart=ecart,
        notes=notes,
        cloture_par_id=user_id,
    )
    db.add(cloture)
    db.flush()
    cloture.fichier_pdf = _generer_pdf(db, cloture)
    db.commit()
    db.refresh(cloture)
    return cloture


def _generer_pdf(db: Session, cloture: ClotureCaisse) -> str:
    """Génère le PDF du rapport Z et retourne son chemin relatif au stockage médias."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    dossier = os.path.join(settings.media_root, "clotures")
    os.makedirs(dossier, exist_ok=True)
    suffixe = f"site{cloture.site_id}" if cloture.site_id else "tous"
    nom_fichier = f"cloture_{cloture.jour.isoformat()}_{suffixe}.pdf"
    chemin = os.path.join(dossier, nom_fichier)

    site = db.get(Site, cloture.site_id) if cloture.site_id else None
    styles = getSampleStyleSheet()

    def _table(data, entetes):
        t = Table([entetes, *data], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    elements = [
        Paragraph("Clôture de caisse (rapport Z)", styles["Title"]),
        Paragraph(f"{cloture.jour.isoformat()} — {site.nom if site else 'Tous les sites'}",
                  styles["Heading3"]),
        Spacer(1, 0.5 * cm),
    ]

    # Ventilation par mode de paiement
    modes = [[m, str(v["nb"]), f'{v["total"]} MAD']
             for m, v in (cloture.detail_modes or {}).items()]
    elements.append(Paragraph("Encaissements par mode", styles["Heading2"]))
    elements.append(_table(modes or [["—", "0", "0 MAD"]], ["Mode", "Tickets", "Total"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Synthèse caisse
    synthese = [
        ["Tickets encaissés", str(cloture.nb_tickets)],
        ["Total théorique", f"{cloture.total_theorique} MAD"],
        ["Fond de caisse", f"{cloture.fond_caisse} MAD"],
        ["Espèces comptées", f"{cloture.montant_compte} MAD"],
        ["Écart de caisse", f"{cloture.ecart} MAD"],
    ]
    elements.append(Paragraph("Synthèse", styles["Heading2"]))
    elements.append(_table(synthese, ["Indicateur", "Valeur"]))
    if cloture.notes:
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(f"Notes : {cloture.notes}", styles["Normal"]))

    SimpleDocTemplate(chemin, pagesize=A4).build(elements)
    return os.path.join("clotures", nom_fichier)
