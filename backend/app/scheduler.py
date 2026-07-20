"""Planification des tâches récurrentes (rapport journalier)."""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.alertes import scanner_absences
from app.services.rapport import generer_rapport_journalier


def _job_rapport_journalier() -> None:
    """Génère le rapport de la journée écoulée et l'envoie."""
    db = SessionLocal()
    try:
        rapport = generer_rapport_journalier(db, date.today())
        # TODO(dev): envoyer le PDF au(x) manager(s) via WhatsApp/email.
        _ = rapport
    finally:
        db.close()


def _job_scan_absences() -> None:
    """Scan périodique des absences (employés planifiés non pointés)."""
    db = SessionLocal()
    try:
        scanner_absences(db)
    finally:
        db.close()


def demarrer_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Africa/Casablanca")
    scheduler.add_job(
        _job_rapport_journalier,
        CronTrigger(hour=settings.report_daily_hour, minute=0),
        id="rapport_journalier",
        replace_existing=True,
    )
    # Toutes les 15 min : détection des absences.
    scheduler.add_job(
        _job_scan_absences,
        IntervalTrigger(minutes=15),
        id="scan_absences",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
