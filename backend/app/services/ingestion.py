"""Ingestion des événements IA → construction/mise à jour des transactions.

Machine à états simple, pilotée par le `track_id` du véhicule :

  ENTREE      -> crée une transaction "en_cours" (heure_entree, photo_entree)
  PLAQUE      -> associe/creé le véhicule, remplit la plaque
  ZONE_ENTER  -> ouvre le chrono de la zone (B/C/D)
  ZONE_EXIT   -> ferme le chrono de la zone, calcule la durée
  BADGE       -> associe l'employé (badge NFC) à la transaction
  SORTIE      -> clôture : durée totale, classification, rapprochement caisse, anomalies

La clôture (rapprochement ticket + persistance des anomalies) est implémentée.
Reste en TODO(dev) : la résolution employé par badge NFC, l'idempotence des
événements, et le déclenchement des alertes temps réel (WhatsApp).
"""
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Anomalie, Forfait, Ticket, Transaction, Vehicule
from app.models.enums import ZoneCode
from app.schemas.event import EventIn, EventType
from app.services import classification as clf
from app.services.anomalie import ContexteTransaction, detecter_anomalies
from app.services.parametres import get_int
from app.services.reconciliation import (
    InfoTransaction,
    TicketCandidat,
    choisir_ticket,
)


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

    # Rapprochement automatique avec la caisse, puis finalisation.
    ticket = _rapprocher_ticket(db, txn)
    finaliser_transaction(db, txn, ticket)
    return txn


def finaliser_transaction(db: Session, txn: Transaction, ticket: Ticket | None) -> Transaction:
    """Classe le forfait effectué, applique le ticket (si fourni) et (re)calcule
    les anomalies.

    Réutilisé par la clôture automatique (_on_sortie) ET le rapprochement manuel.
    Idempotent : purge d'abord les anomalies existantes de la transaction.
    """
    # 1) Classification du forfait effectué (piloté par les forfaits en base)
    zones = _zones_visitees(txn)
    duree_min = (txn.duree_totale / 60) if txn.duree_totale else None
    forfaits_def = _forfaits_def(db)
    forfait_detecte = clf.deduire_forfait_effectue(zones, forfaits_def)
    txn.forfait_detecte = forfait_detecte.nom if forfait_detecte else None

    # 2) Application du ticket (forfait payé)
    forfait_paye: clf.ForfaitDef | None = None
    if ticket is not None:
        txn.forfait_id = ticket.forfait_id
        forfait_paye = next((f for f in forfaits_def if f.nom == ticket.forfait.nom), None)
        ticket.statut = "rapproche"
        ticket.transaction_id = txn.id
        txn.conforme = (
            clf.est_conforme(forfait_paye, zones, duree_min)
            if forfait_paye else None
        )
    else:
        txn.conforme = None

    # 3) (Re)détection des anomalies — on repart d'une table propre pour cette txn.
    db.query(Anomalie).filter(Anomalie.transaction_id == txn.id).delete()
    ctx = ContexteTransaction(
        forfait_paye=forfait_paye,
        forfait_detecte=forfait_detecte,
        zones_visitees=zones,
        duree_totale_min=duree_min,
        plaque_lue=txn.vehicule_id is not None,
    )
    for a in detecter_anomalies(ctx):
        db.add(Anomalie(
            transaction_id=txn.id,
            type=a.type,
            severite=a.severite,
            description=a.description,
            photo=txn.photo_entree,
        ))
        # TODO(dev): pour severite CRITIQUE/HAUTE, déclencher l'alerte WhatsApp
        #   (services.notification.envoyer_alerte_whatsapp) via une tâche de fond,
        #   puis marquer Anomalie.notifie = True.
    return txn


def _forfaits_def(db: Session) -> list[clf.ForfaitDef]:
    """Charge les forfaits de la base sous forme de définitions pures."""
    return [
        clf.ForfaitDef(
            nom=f.nom,
            zones_requises=frozenset(f.zones_requises or []),
            temps_min=f.temps_min,
            prix=float(f.prix),
        )
        for f in db.scalars(select(Forfait)).all()
    ]


def _rapprocher_ticket(db: Session, txn: Transaction) -> Ticket | None:
    """Cherche le ticket de caisse correspondant à la transaction clôturée."""
    # Tickets ouverts de la journée (borne raisonnable pour le rapprochement).
    debut_jour = datetime.combine(date.today(), time.min)
    tickets = db.scalars(
        select(Ticket).where(
            Ticket.statut == "ouvert",
            Ticket.heure >= debut_jour,
        )
    ).all()

    plaque = txn.vehicule.plaque if txn.vehicule else None
    candidats = [TicketCandidat(id=t.id, plaque=t.plaque, heure=t.heure) for t in tickets]
    choisi = choisir_ticket(
        InfoTransaction(plaque=plaque, heure_entree=txn.heure_entree,
                        heure_sortie=txn.heure_sortie),
        candidats,
        fenetre_minutes=get_int(db, "fenetre_rapprochement_minutes", 30),
    )
    if choisi is None:
        return None
    return next((t for t in tickets if t.id == choisi.id), None)


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
