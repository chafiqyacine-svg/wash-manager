"""Ingestion des événements IA → construction/mise à jour des transactions.

Machine à états simple, pilotée par le `track_id` du véhicule :

  ENTREE      -> crée une transaction "en_cours" (heure_entree, photo_entree)
  PLAQUE      -> associe/creé le véhicule, remplit la plaque
  ZONE_ENTER  -> ouvre le chrono de la zone (B/C/D)
  ZONE_EXIT   -> ferme le chrono de la zone, calcule la durée
  BADGE       -> associe l'employé (badge NFC) à la transaction
  SORTIE      -> clôture : durée totale, classification, rapprochement POS, anomalies

Ce service est un SQUELETTE : la structure et les branches sont posées, mais le
détail (rapprochement POS, gestion des cas limites, idempotence) est à finir.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction, Vehicule
from app.models.enums import ForfaitNom, ZoneCode
from app.schemas.event import EventIn, EventType
from app.services import classification as clf
from app.services.anomalie import ContexteTransaction, detecter_anomalies


def traiter_evenement(db: Session, event: EventIn) -> Transaction | None:
    """Point d'entrée unique appelé par la route /events."""
    handler = {
        EventType.ENTREE: _on_entree,
        EventType.PLAQUE: _on_plaque,
        EventType.ZONE_ENTER: _on_zone_enter,
        EventType.ZONE_EXIT: _on_zone_exit,
        EventType.BADGE: _on_badge,
        EventType.SORTIE: _on_sortie,
    }[event.type]
    txn = handler(db, event)
    db.commit()
    return txn


def _get_transaction_active(db: Session, track_id: str) -> Transaction | None:
    return db.scalar(
        select(Transaction).where(
            Transaction.track_id == track_id,
            Transaction.statut == "en_cours",
        )
    )


def _on_entree(db: Session, event: EventIn) -> Transaction:
    txn = Transaction(
        track_id=event.track_id,
        heure_entree=event.timestamp,
        photo_entree=event.photo,
        statut="en_cours",
    )
    db.add(txn)
    return txn


def _on_plaque(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None or not event.plaque:
        # TODO(dev): si la plaque n'a pas pu être lue (confiance faible),
        #   stocker la capture pour saisie manuelle et lever PLAQUE_NON_LUE.
        return txn
    vehicule = db.scalar(select(Vehicule).where(Vehicule.plaque == event.plaque))
    if vehicule is None:
        vehicule = Vehicule(plaque=event.plaque, premiere_visite=event.timestamp,
                            nombre_visites=0)
        db.add(vehicule)
        db.flush()
    vehicule.derniere_visite = event.timestamp
    vehicule.nombre_visites += 1
    txn.vehicule_id = vehicule.id
    return txn


def _on_zone_enter(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None or event.zone is None:
        return txn
    _set_zone_field(txn, event.zone, "debut", event.timestamp)
    return txn


def _on_zone_exit(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None or event.zone is None:
        return txn
    _set_zone_field(txn, event.zone, "fin", event.timestamp)
    _calculer_duree_zone(txn, event.zone)
    return txn


def _on_badge(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None or not event.badge_nfc_id:
        return txn
    # TODO(dev): résoudre l'employé à partir du badge NFC (table employes)
    #   et affecter txn.employe_id. Gérer le cas badge inconnu.
    return txn


def _on_sortie(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None:
        return None

    txn.heure_sortie = event.timestamp
    txn.photo_sortie = event.photo or txn.photo_sortie
    if txn.heure_entree:
        txn.duree_totale = int((txn.heure_sortie - txn.heure_entree).total_seconds())
    txn.statut = "cloturee"

    # 1) Classification du forfait effectué
    zones = _zones_visitees(txn)
    duree_min = (txn.duree_totale / 60) if txn.duree_totale else None
    parcours = clf.ParcoursVehicule(zones_visitees=zones, duree_totale_min=duree_min)
    forfait_detecte = clf.deduire_forfait_effectue(parcours)
    txn.forfait_detecte = forfait_detecte.value

    # 2) Rapprochement POS
    # TODO(dev): récupérer le ticket POS correspondant (par plaque et/ou fenêtre
    #   horaire) via le connecteur caisse, en déduire forfait_paye + forfait_id +
    #   txn.conforme. Ci-dessous : placeholder à remplacer.
    forfait_paye: ForfaitNom | None = None  # TODO(dev)

    if forfait_paye is not None:
        txn.conforme = clf.est_conforme(forfait_paye, parcours, temps_min_paye=0)  # TODO(dev): vrai seuil

    # 3) Détection d'anomalies
    ctx = ContexteTransaction(
        forfait_paye=forfait_paye,
        forfait_detecte=forfait_detecte,
        zones_visitees=zones,
        duree_totale_min=duree_min,
        plaque_lue=txn.vehicule_id is not None,
    )
    anomalies = detecter_anomalies(ctx)
    # TODO(dev): persister ces anomalies (models.Anomalie) liées à txn.id
    #   puis déclencher services.notification pour les sévérités CRITIQUE/HAUTE.
    _ = anomalies

    return txn


# ─── Helpers zones ───────────────────────────────────────────────────────────
_ZONE_PREFIX = {
    ZoneCode.LAVAGE_EXT.value: "zone_b",
    ZoneCode.ASPIRATION.value: "zone_c",
    ZoneCode.POLISH.value: "zone_d",
}


def _set_zone_field(txn: Transaction, zone: str, suffix: str, value: datetime) -> None:
    prefix = _ZONE_PREFIX.get(zone)
    if prefix:
        setattr(txn, f"{prefix}_{suffix}", value)


def _calculer_duree_zone(txn: Transaction, zone: str) -> None:
    prefix = _ZONE_PREFIX.get(zone)
    if not prefix:
        return
    debut = getattr(txn, f"{prefix}_debut")
    fin = getattr(txn, f"{prefix}_fin")
    if debut and fin:
        setattr(txn, f"{prefix}_duree", int((fin - debut).total_seconds()))


def _zones_visitees(txn: Transaction) -> set[str]:
    """Une zone est "visitée" si son horodatage de début est renseigné."""
    zones = set()
    if txn.zone_b_debut:
        zones.add(ZoneCode.LAVAGE_EXT.value)
    if txn.zone_c_debut:
        zones.add(ZoneCode.ASPIRATION.value)
    if txn.zone_d_debut:
        zones.add(ZoneCode.POLISH.value)
    return zones
