"""Indicateurs RH : présence, ponctualité, temps actif vs temps mort.

Croise trois sources par employé et par jour :
  - planning         : HoraireEmploye (créneau prévu ce jour)
  - pointages        : Pointage (arrivée/départ réels, selfies horodatés)
  - lavages effectués: Transaction (temps de travail réel)

Retourne une ligne par employé, prête pour le tableau de présence.
"""
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employe, HoraireEmploye, Pointage, Transaction


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise en UTC-aware (SQLite renvoie des datetimes naïfs)."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def presence_du_jour(db: Session, jour: date, site_id: int | None = None) -> list[dict]:
    debut = datetime.combine(jour, time.min, tzinfo=timezone.utc)
    fin = debut + timedelta(days=1)
    weekday = jour.weekday()  # 0=lundi … 6=dimanche
    maintenant = datetime.now(timezone.utc)

    emp_stmt = select(Employe).where(Employe.actif.is_(True))
    if site_id:
        emp_stmt = emp_stmt.where(Employe.site_id == site_id)
    employes = db.scalars(emp_stmt).all()

    lignes = []
    for e in employes:
        # 1) Planning du jour
        creneau = db.scalar(
            select(HoraireEmploye).where(
                HoraireEmploye.employe_id == e.id, HoraireEmploye.jour == weekday
            )
        )

        # 2) Pointages du jour
        pointages = db.scalars(
            select(Pointage).where(
                Pointage.employe_id == e.id,
                Pointage.heure >= debut, Pointage.heure < fin,
            ).order_by(Pointage.heure)
        ).all()
        arrivees = [p for p in pointages if p.type == "arrivee"]
        departs = [p for p in pointages if p.type == "depart"]
        arrivee = _aware(arrivees[0].heure) if arrivees else None
        depart = _aware(departs[-1].heure) if departs else None

        # 3) Temps de travail réel (somme des lavages du jour)
        durees = db.scalars(
            select(Transaction.duree_totale).where(
                Transaction.employe_id == e.id,
                Transaction.statut == "cloturee",
                Transaction.heure_sortie >= debut, Transaction.heure_sortie < fin,
                Transaction.duree_totale.is_not(None),
            )
        ).all()
        temps_actif_min = round(sum(durees) / 60, 1) if durees else 0.0

        # Statut de présence
        if creneau is None and arrivee is None:
            statut = "non_planifie"
        elif arrivee is None:
            statut = "absent"
        else:
            statut = "present"

        # Ponctualité (retard = arrivée - début de créneau)
        retard_min = None
        if creneau is not None and arrivee is not None:
            debut_prevu = datetime.combine(jour, creneau.debut, tzinfo=timezone.utc)
            retard_min = max(0, round((arrivee - debut_prevu).total_seconds() / 60))

        # Temps de présence (départ - arrivée, ou maintenant si encore présent)
        temps_present_min = None
        if arrivee is not None:
            ref = depart or maintenant
            temps_present_min = max(0, round((ref - arrivee).total_seconds() / 60))

        temps_mort_min = None
        productivite_pct = None
        if temps_present_min:
            temps_mort_min = max(0, round(temps_present_min - temps_actif_min))
            productivite_pct = round(temps_actif_min / temps_present_min * 100, 1)

        lignes.append({
            "employe_id": e.id,
            "nom": e.nom,
            "site_id": e.site_id,
            "planifie": creneau is not None,
            "creneau": (f"{creneau.debut.strftime('%H:%M')}–{creneau.fin.strftime('%H:%M')}"
                        if creneau else None),
            "arrivee": arrivee,
            "depart": depart,
            "statut": statut,
            "retard_min": retard_min,
            "temps_present_min": temps_present_min,
            "temps_actif_min": temps_actif_min,
            "temps_mort_min": temps_mort_min,
            "productivite_pct": productivite_pct,
        })
    return lignes
