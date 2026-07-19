"""Génération du rapport journalier (agrégats + PDF) et planification.

Chaque soir (settings.report_daily_hour), un job APScheduler appelle
`generer_rapport_journalier`. Le rapport agrège les transactions du jour,
calcule les KPI et la performance par employé, génère un PDF (ReportLab) et
l'archive.

Les agrégations et la génération PDF sont IMPLÉMENTÉES. Reste en TODO(dev) :
l'ajout d'un graphique horaire dans le PDF et l'envoi WhatsApp/email.
"""
import os
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Anomalie, Employe, Forfait, RapportJournalier, Transaction


def generer_rapport_journalier(db: Session, jour: date) -> RapportJournalier:
    """Construit (ou met à jour) le rapport du jour donné."""
    stats = _agreger_journee(db, jour)

    # Upsert : un seul rapport par jour.
    rapport = db.scalar(select(RapportJournalier).where(RapportJournalier.date == jour))
    if rapport is None:
        rapport = RapportJournalier(date=jour)
        db.add(rapport)

    rapport.total_vehicules = stats["total_vehicules"]
    rapport.total_ca = stats["total_ca"]
    rapport.repartition_forfaits = stats["repartition_forfaits"]
    rapport.taux_conformite = stats["taux_conformite"]
    rapport.nombre_anomalies = stats["nombre_anomalies"]
    rapport.performance_employes = stats["performance_employes"]
    db.flush()

    rapport.fichier_pdf = _generer_pdf(rapport, stats)
    db.commit()
    db.refresh(rapport)
    return rapport


def _agreger_journee(db: Session, jour: date) -> dict:
    """Calcule les KPI de la journée à partir des transactions clôturées."""
    debut = datetime.combine(jour, time.min)
    fin = debut + timedelta(days=1)

    txns = db.scalars(
        select(Transaction).where(
            Transaction.statut == "cloturee",
            Transaction.heure_sortie >= debut,
            Transaction.heure_sortie < fin,
        )
    ).all()

    prix_forfait = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}
    noms_employes = {e.id: e.nom for e in db.scalars(select(Employe)).all()}

    total_vehicules = len(txns)
    total_ca = sum(prix_forfait.get(t.forfait_id, 0.0) for t in txns if t.forfait_id)
    repartition = Counter(t.forfait_detecte for t in txns if t.forfait_detecte)

    evaluees = [t for t in txns if t.conforme is not None]
    conformes = sum(1 for t in evaluees if t.conforme)
    taux_conformite = round(conformes / len(evaluees) * 100, 1) if evaluees else 0.0

    nombre_anomalies = db.query(Anomalie).filter(
        Anomalie.heure >= debut, Anomalie.heure < fin
    ).count()

    return {
        "total_vehicules": total_vehicules,
        "total_ca": round(total_ca, 2),
        "repartition_forfaits": dict(repartition),
        "taux_conformite": taux_conformite,
        "nombre_anomalies": nombre_anomalies,
        "performance_employes": _perf_employes(txns, prix_forfait, noms_employes),
        # Volume par heure (pour le graphique — cf. TODO PDF).
        "volume_horaire": _volume_horaire(txns),
    }


def _perf_employes(txns, prix_forfait, noms_employes) -> list[dict]:
    """Métriques par employé (cf. tableau 8.2)."""
    par_employe = defaultdict(list)
    for t in txns:
        if t.employe_id:
            par_employe[t.employe_id].append(t)

    perf = []
    for employe_id, lignes in par_employe.items():
        durees = [t.duree_totale for t in lignes if t.duree_totale]
        evaluees = [t for t in lignes if t.conforme is not None]
        conformes = sum(1 for t in evaluees if t.conforme)
        taux = round(conformes / len(evaluees) * 100, 1) if evaluees else 0.0
        temps_moyen = round(sum(durees) / len(durees) / 60, 1) if durees else 0.0
        revenus = round(sum(prix_forfait.get(t.forfait_id, 0.0) for t in lignes if t.forfait_id), 2)
        perf.append({
            "employe_id": employe_id,
            "nom": noms_employes.get(employe_id, f"#{employe_id}"),
            "vehicules": len(lignes),
            "temps_moyen_min": temps_moyen,
            "taux_conformite": taux,
            "revenus": revenus,
            # Score qualité : composite simple (conformité + productivité).
            # TODO(dev): rendre la pondération configurable (cf. section 8.2).
            "score_qualite": round(taux, 1),
        })
    perf.sort(key=lambda p: p["score_qualite"], reverse=True)
    return perf


def _volume_horaire(txns) -> dict[int, int]:
    heures = Counter(t.heure_entree.hour for t in txns if t.heure_entree)
    return {h: heures.get(h, 0) for h in range(24)}


def _generer_pdf(rapport: RapportJournalier, stats: dict) -> str:
    """Génère le PDF du rapport et retourne son chemin relatif au stockage médias."""
    # Import local : reportlab n'est requis que pour cette fonction.
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    dossier = os.path.join(settings.media_root, "reports")
    os.makedirs(dossier, exist_ok=True)
    nom_fichier = f"rapport_{rapport.date.isoformat()}.pdf"
    chemin = os.path.join(dossier, nom_fichier)

    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Rapport journalier — {rapport.date.isoformat()}", styles["Title"]),
        Spacer(1, 0.5 * cm),
    ]

    # Résumé du jour
    resume = [
        ["Véhicules", str(rapport.total_vehicules)],
        ["Chiffre d'affaires", f"{rapport.total_ca} MAD"],
        ["Taux de conformité", f"{rapport.taux_conformite} %"],
        ["Anomalies", str(rapport.nombre_anomalies)],
    ]
    elements.append(_table(resume, ["Indicateur", "Valeur"], colors.HexColor("#0f172a")))
    elements.append(Spacer(1, 0.5 * cm))

    # Répartition des forfaits
    if rapport.repartition_forfaits:
        rep = [[k, str(v)] for k, v in rapport.repartition_forfaits.items()]
        elements.append(Paragraph("Répartition des forfaits", styles["Heading2"]))
        elements.append(_table(rep, ["Forfait", "Nombre"], colors.HexColor("#334155")))
        elements.append(Spacer(1, 0.5 * cm))

    # Performance des employés
    if rapport.performance_employes:
        lignes = [
            [p["nom"], str(p["vehicules"]), f'{p["temps_moyen_min"]}',
             f'{p["taux_conformite"]}%', f'{p["revenus"]}']
            for p in rapport.performance_employes
        ]
        elements.append(Paragraph("Performance des employés", styles["Heading2"]))
        elements.append(_table(
            lignes,
            ["Employé", "Véhicules", "Tps moy (min)", "Conformité", "Revenus"],
            colors.HexColor("#334155"),
        ))

    # TODO(dev): ajouter un graphique du volume horaire (stats["volume_horaire"])
    #   et les comparaisons vs veille / semaine précédente / moyenne mensuelle.

    SimpleDocTemplate(chemin, pagesize=A4).build(elements)
    return os.path.join("reports", nom_fichier)


def _table(data, entetes, couleur_entete):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    t = Table([entetes, *data], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), couleur_entete),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return t
