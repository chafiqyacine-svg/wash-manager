"""Envoi d'alertes (WhatsApp / email) + journalisation.

Architecture posée, envois réels branchables. Chaque alerte est enregistrée
(table `notifications`) avec son statut :
  - "envoye"  : transmise par un canal réel ;
  - "simule"  : aucun canal configuré → trace conservée, à transmettre plus tard ;
  - "echec"   : canal configuré mais l'envoi a échoué.

Les canaux réels (SMTP, API WhatsApp) sont des points d'extension TODO(dev) :
la logique de déclenchement/dispatch/traçage — testable — est complète.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Notification

SEVERITES_ALERTE = {"haute", "critique"}


def _canaux_configures() -> list[str]:
    """Canaux réellement utilisables (selon la config). Vide → mode simulé."""
    canaux = []
    if settings.whatsapp_api_url and settings.whatsapp_api_token and settings.manager_numbers:
        canaux.append("whatsapp")
    if settings.smtp_host and settings.emails_alerte:
        canaux.append("email")
    return canaux


def _envoyer_whatsapp(destinataire: str, sujet: str, message: str) -> bool:
    # TODO(dev): POST vers settings.whatsapp_api_url avec le token (httpx).
    return False


def _envoyer_email(destinataire: str, sujet: str, message: str) -> bool:
    # TODO(dev): envoyer via smtplib (settings.smtp_*).
    return False


_EXPEDITEURS = {"whatsapp": _envoyer_whatsapp, "email": _envoyer_email}


def _destinataires(canal: str) -> list[str]:
    return settings.manager_numbers if canal == "whatsapp" else settings.emails_alerte


def notifier(db: Session, sujet: str, message: str, *, severite: str | None = None,
             site_id: int | None = None, ref_type: str | None = None,
             ref_id: int | None = None, commit: bool = True) -> list[Notification]:
    """Envoie une alerte sur tous les canaux configurés et la journalise.

    Sans canal configuré, une entrée « simule » (canal=log) est tout de même
    créée : rien n'est perdu, le gérant voit l'alerte dans l'historique.
    """
    canaux = _canaux_configures()
    entrees: list[Notification] = []

    cibles = [(c, d) for c in canaux for d in _destinataires(c)] or [("log", None)]
    for canal, destinataire in cibles:
        if canal == "log":
            statut = "simule"
        else:
            ok = _EXPEDITEURS[canal](destinataire, sujet, message)
            statut = "envoye" if ok else "echec"
        entree = Notification(
            canal=canal, destinataire=destinataire, sujet=sujet, message=message,
            severite=severite, statut=statut, site_id=site_id,
            ref_type=ref_type, ref_id=ref_id,
        )
        db.add(entree)
        entrees.append(entree)

    if commit:
        db.commit()
    return entrees


def notifier_anomalie(db: Session, *, type_: str, severite: str, description: str | None,
                      site_id: int | None = None, anomalie_id: int | None = None,
                      commit: bool = False) -> list[Notification]:
    """Déclenche une alerte pour une anomalie grave (severite haute/critique)."""
    if severite not in SEVERITES_ALERTE:
        return []
    sujet = f"[{severite.upper()}] Anomalie : {type_}"
    message = description or f"Anomalie {type_} détectée."
    return notifier(db, sujet, message, severite=severite, site_id=site_id,
                    ref_type="anomalie", ref_id=anomalie_id, commit=commit)
