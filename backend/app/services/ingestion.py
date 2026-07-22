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
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session


def _duree_secondes(debut: datetime, fin: datetime) -> int:
    """Durée en secondes, robuste aux fuseaux (SQLite naïf vs PostgreSQL aware)."""
    if debut.tzinfo is None and fin.tzinfo is not None:
        debut = debut.replace(tzinfo=fin.tzinfo)
    elif fin.tzinfo is None and debut.tzinfo is not None:
        fin = fin.replace(tzinfo=debut.tzinfo)
    return int((fin - debut).total_seconds())

from app.models import (
    Anomalie,
    Bay,
    Employe,
    Forfait,
    ForfaitProduit,
    HoraireSite,
    Produit,
    Ticket,
    Transaction,
    Vehicule,
)
from app.models.enums import AnomalieSeverite, AnomalieType, ZoneCode
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
    # Le tracker réattribue les track_id après le départ d'un véhicule ; si une
    # SORTIE a été manquée, une ancienne transaction peut rester "en_cours" avec
    # le même track_id. On retient donc TOUJOURS la plus récente (le véhicule
    # courant), pas une correspondance arbitraire.
    return db.scalar(
        select(Transaction)
        .where(
            Transaction.track_id == track_id,
            Transaction.statut == "en_cours",
        )
        .order_by(Transaction.id.desc())
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
    """Identifie l'employé et le relie à la transaction.

    Deux mécanismes acceptés :
      - badge NFC (`badge_nfc_id`) — déterministe ;
      - couleur de gilet (`couleur_gilet`) détectée par vision — le pipeline
        envoie la couleur, on la rapproche de l'employé correspondant.
    """
    txn = _get_transaction_active(db, event.track_id)
    if txn is None:
        return txn
    employe = None
    if event.badge_nfc_id:
        employe = db.scalar(select(Employe).where(Employe.badge_nfc_id == event.badge_nfc_id))
    elif event.couleur_gilet:
        employe = db.scalar(select(Employe).where(Employe.couleur_gilet == event.couleur_gilet))
    if employe is not None:
        txn.employe_id = employe.id
    # TODO(dev): identification inconnue -> journaliser / anomalie d'identification.
    return txn


def _on_sortie(db: Session, event: EventIn) -> Transaction | None:
    txn = _get_transaction_active(db, event.track_id)
    if txn is None:
        return None

    txn.heure_sortie = event.timestamp
    txn.photo_sortie = event.photo or txn.photo_sortie
    if txn.heure_entree:
        txn.duree_totale = _duree_secondes(txn.heure_entree, txn.heure_sortie)
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

    # Consommation d'inventaire selon la recette du forfait effectué.
    _consommer_produits(db, txn, forfait_detecte)

    # Anomalie « lavage hors horaires d'ouverture » (dépend du site + horaires).
    if _hors_horaires_ouverture(db, txn):
        db.add(Anomalie(
            transaction_id=txn.id,
            type=AnomalieType.LAVAGE_HORS_HORAIRES,
            severite=AnomalieSeverite.MOYENNE,
            description="Lavage effectué en dehors des horaires d'ouverture du site.",
            photo=txn.photo_entree,
        ))
    return txn


def _consommer_produits(db: Session, txn: Transaction, forfait_detecte) -> None:
    """Décrémente le stock des produits consommés par le forfait effectué.

    Consomme 1 / lavages_par_unite par lavage. Ne décrémente que les produits
    situés au site du lavage (via la baie) ; si le lavage n'a pas de baie, tous
    les produits de la recette sont concernés.
    """
    # Idempotence : ne consommer qu'une seule fois par transaction (évite le
    # double décrément si finaliser_transaction est rappelée, ex. rapprochement
    # manuel).
    if txn.inventaire_consomme:
        return

    # Forfait effectif : le forfait facturé sinon celui détecté.
    forfait_id = txn.forfait_id
    if forfait_id is None and forfait_detecte is not None:
        f = db.scalar(select(Forfait).where(Forfait.nom == forfait_detecte.nom))
        forfait_id = f.id if f else None
    if forfait_id is None:
        return

    site_id = None
    if txn.bay_id is not None:
        bay = db.get(Bay, txn.bay_id)
        site_id = bay.site_id if bay else None

    recette = db.scalars(
        select(ForfaitProduit).where(ForfaitProduit.forfait_id == forfait_id)
    ).all()
    for ligne in recette:
        produit: Produit | None = ligne.produit
        if produit is None or not ligne.lavages_par_unite:
            continue
        # N'affecte que le stock du site du lavage (si connu).
        if site_id is not None and produit.site_id is not None and produit.site_id != site_id:
            continue
        produit.quantite = max(0, float(produit.quantite) - 1 / ligne.lavages_par_unite)
        # TODO(dev): si produit.quantite <= seuil_alerte -> alerte réappro.

    txn.inventaire_consomme = True


def consommer_inventaire(db: Session, txn: Transaction) -> None:
    """Point d'entrée public : consomme l'inventaire d'un lavage clôturé
    (mode manuel via la file d'attente). Idempotent."""
    _consommer_produits(db, txn, None)


def _hors_horaires_ouverture(db: Session, txn: Transaction) -> bool:
    """True si l'heure d'entrée est hors des horaires d'ouverture du site."""
    if txn.heure_entree is None or txn.bay_id is None:
        return False
    bay = db.get(Bay, txn.bay_id)
    if bay is None:
        return False
    entree = txn.heure_entree
    horaire = db.scalar(
        select(HoraireSite).where(
            HoraireSite.site_id == bay.site_id,
            HoraireSite.jour == entree.weekday(),
        )
    )
    if horaire is None:
        return True  # site fermé ce jour-là
    return not (horaire.heure_ouverture <= entree.time() <= horaire.heure_fermeture)


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
    # Anti-concurrence : on VERROUILLE le ticket choisi (SELECT ... FOR UPDATE en
    # PostgreSQL) et on revérifie qu'il est toujours « ouvert ». Si une autre
    # clôture simultanée l'a déjà pris, on renonce (pas de double rapprochement).
    return db.scalar(
        select(Ticket)
        .where(Ticket.id == choisi.id, Ticket.statut == "ouvert")
        .with_for_update()
    )


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
        setattr(txn, f"{prefix}_duree", _duree_secondes(debut, fin))


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
