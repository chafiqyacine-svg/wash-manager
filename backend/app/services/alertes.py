"""Alertes RH : retards (à la pointe) et absences (par scan planifié).

Une alerte = une anomalie persistée (type RETARD/ABSENCE, liée à l'employé) +
une diffusion temps réel (WebSocket) + une notification (WhatsApp si configuré,
sinon journalisée). Elle apparaît donc dans les Anomalies et Recent Events.
"""
import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Anomalie, Employe, HoraireEmploye, Pointage
from app.models.enums import AnomalieSeverite, AnomalieType
from app.services.parametres import get_int

logger = logging.getLogger("alertes")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def creer_alerte(db: Session, employe_id: int, type_: AnomalieType,
                 severite: AnomalieSeverite, description: str) -> Anomalie:
    """Persiste l'anomalie RH, diffuse en temps réel et notifie."""
    anomalie = Anomalie(employe_id=employe_id, type=type_, severite=severite,
                        description=description)
    db.add(anomalie)
    db.commit()
    db.refresh(anomalie)

    # Diffusion temps réel (import local pour éviter les cycles).
    try:
        from app.api.routes.live import manager as live_manager
        live_manager.notifier({"type": "update", "source": "alerte"})
    except Exception:  # pragma: no cover
        pass

    # Notification (WhatsApp si configuré ; sinon on journalise).
    # TODO(dev): envoyer via services.notification.envoyer_alerte_whatsapp en
    #   tâche de fond, puis marquer anomalie.notifie = True.
    logger.warning("ALERTE RH [%s] employé %s : %s", type_.value, employe_id, description)
    return anomalie


def verifier_retard(db: Session, employe_id: int, arrivee: datetime) -> Anomalie | None:
    """Appelée au pointage d'arrivée : lève une alerte si retard au-delà de la tolérance."""
    jour = _aware(arrivee).date()
    creneau = db.scalar(
        select(HoraireEmploye).where(
            HoraireEmploye.employe_id == employe_id,
            HoraireEmploye.jour == jour.weekday(),
        )
    )
    if creneau is None:
        return None
    debut_prevu = datetime.combine(jour, creneau.debut, tzinfo=timezone.utc)
    retard = round((_aware(arrivee) - debut_prevu).total_seconds() / 60)
    if retard <= get_int(db, "tolerance_retard_minutes", 10):
        return None
    employe = db.get(Employe, employe_id)
    nom = employe.nom if employe else f"#{employe_id}"
    return creer_alerte(
        db, employe_id, AnomalieType.RETARD, AnomalieSeverite.MOYENNE,
        f"{nom} en retard de {retard} min (arrivée {arrivee.strftime('%H:%M')}).",
    )


def scanner_absences(db: Session, maintenant: datetime | None = None) -> list[Anomalie]:
    """Scan planifié : déclare absents les employés planifiés non pointés au-delà
    du délai après le début de leur créneau (une seule alerte/employé/jour)."""
    maintenant = _aware(maintenant or datetime.now(timezone.utc))
    jour = maintenant.date()
    debut_jour = datetime.combine(jour, time.min, tzinfo=timezone.utc)
    delai = get_int(db, "delai_absence_minutes", 30)

    creneaux = db.scalars(
        select(HoraireEmploye).where(HoraireEmploye.jour == jour.weekday())
    ).all()

    alertes = []
    for c in creneaux:
        debut_prevu = datetime.combine(jour, c.debut, tzinfo=timezone.utc)
        if maintenant < debut_prevu + timedelta(minutes=delai):
            continue  # trop tôt pour conclure à l'absence
        # A-t-il pointé son arrivée aujourd'hui ?
        pointe = db.scalar(
            select(Pointage.id).where(
                Pointage.employe_id == c.employe_id,
                Pointage.type == "arrivee",
                Pointage.heure >= debut_jour,
            )
        )
        if pointe is not None:
            continue
        # Déjà une alerte d'absence aujourd'hui ?
        deja = db.scalar(
            select(Anomalie.id).where(
                Anomalie.employe_id == c.employe_id,
                Anomalie.type == AnomalieType.ABSENCE,
                Anomalie.heure >= debut_jour,
            )
        )
        if deja is not None:
            continue
        employe = db.get(Employe, c.employe_id)
        nom = employe.nom if employe else f"#{c.employe_id}"
        alertes.append(creer_alerte(
            db, c.employe_id, AnomalieType.ABSENCE, AnomalieSeverite.HAUTE,
            f"{nom} absent : aucun pointage pour le créneau de "
            f"{c.debut.strftime('%H:%M')}.",
        ))
    return alertes
