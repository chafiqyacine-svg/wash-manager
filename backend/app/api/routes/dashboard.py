"""KPI agrégés pour le dashboard (vue temps réel + chiffres du jour)."""
from collections import Counter
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.core.database import get_db
from app.models import Anomalie, Bay, Forfait, Ticket, Transaction
from app.models.enums import StatutLavage, ZoneCode

router = APIRouter(prefix="/dashboard", tags=["dashboard"],
                   dependencies=[Depends(get_current_user)])


def _bay_ids_du_site(db: Session, site_id: int | None) -> list[int] | None:
    """IDs des baies d'un site (None => tous les sites, pas de filtre)."""
    if not site_id:
        return None
    return list(db.scalars(select(Bay.id).where(Bay.site_id == site_id)).all())


def _delta_pct(courant: float, precedent: float) -> float | None:
    if precedent == 0:
        return None
    return round((courant - precedent) / precedent * 100, 1)


@router.get("/kpi")
def kpi_du_jour(db: Session = Depends(get_db)) -> dict:
    """KPI du jour : nb véhicules, CA, temps moyen, taux de conformité."""
    debut = datetime.combine(date.today(), time.min)
    fin = debut + timedelta(days=1)

    txns = db.scalars(
        select(Transaction).where(
            Transaction.statut == "cloturee",
            Transaction.heure_sortie >= debut,
            Transaction.heure_sortie < fin,
        )
    ).all()
    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}

    ca = sum(prix.get(t.forfait_id, 0.0) for t in txns if t.forfait_id)
    durees = [t.duree_totale for t in txns if t.duree_totale]
    temps_moyen = round(sum(durees) / len(durees) / 60, 1) if durees else 0.0
    evaluees = [t for t in txns if t.conforme is not None]
    conformes = sum(1 for t in evaluees if t.conforme)
    taux = round(conformes / len(evaluees) * 100, 1) if evaluees else 0.0

    anomalies_ouvertes = db.query(Anomalie).filter(Anomalie.resolu.is_(False)).count()

    return {
        "vehicules": len(txns),
        "chiffre_affaires": round(ca, 2),
        "temps_moyen_min": temps_moyen,
        "taux_conformite": taux,
        "anomalies_ouvertes": anomalies_ouvertes,
    }


# Colonnes de début de zone -> code zone (pour déduire la position courante).
_ZONE_DEBUTS = [
    ("zone_d_debut", ZoneCode.POLISH.value),
    ("zone_c_debut", ZoneCode.ASPIRATION.value),
    ("zone_b_debut", ZoneCode.LAVAGE_EXT.value),
]


@router.get("/en-cours")
def vehicules_en_cours(db: Session = Depends(get_db)) -> list[dict]:
    """Véhicules actuellement sur le site (transactions statut=en_cours)."""
    txns = db.scalars(
        select(Transaction).where(Transaction.statut == "en_cours")
        .order_by(Transaction.heure_entree)
    ).all()

    resultat = []
    for t in txns:
        # Zone courante = la zone la plus avancée dont le début est renseigné.
        zone = next((code for champ, code in _ZONE_DEBUTS if getattr(t, champ)), ZoneCode.ENTREE.value)
        resultat.append({
            "transaction_id": t.id,
            "track_id": t.track_id,
            "plaque": t.vehicule.plaque if t.vehicule else None,
            "heure_entree": t.heure_entree,
            "zone_courante": zone,
        })
    return resultat


@router.get("/apercu")
def apercu(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site)) -> dict:
    """4 cartes d'en-tête (style « Clean It ») avec évolution vs la veille.

    - ongoing  : lavages en cours (instantané)
    - in_order : tickets payés en attente de lavage
    - completed: lavages terminés aujourd'hui
    - revenue  : chiffre d'affaires du jour
    """
    bay_ids = _bay_ids_du_site(db, site_id)
    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}

    def txns_du_jour(jour: date, statut: str) -> list[Transaction]:
        d0 = datetime.combine(jour, time.min)
        d1 = d0 + timedelta(days=1)
        col = Transaction.heure_sortie if statut == "cloturee" else Transaction.heure_entree
        stmt = select(Transaction).where(Transaction.statut == statut, col >= d0, col < d1)
        if bay_ids is not None:
            stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
        return db.scalars(stmt).all()

    hier = date.today() - timedelta(days=1)
    completed_today = txns_du_jour(date.today(), "cloturee")
    completed_hier = txns_du_jour(hier, "cloturee")
    revenue_today = sum(prix.get(t.forfait_id, 0.0) for t in completed_today if t.forfait_id)
    revenue_hier = sum(prix.get(t.forfait_id, 0.0) for t in completed_hier if t.forfait_id)

    ongoing_stmt = select(Transaction).where(Transaction.statut == "en_cours")
    if bay_ids is not None:
        ongoing_stmt = ongoing_stmt.where(Transaction.bay_id.in_(bay_ids))
    ongoing = len(db.scalars(ongoing_stmt).all())

    in_order = db.query(Ticket).filter(Ticket.statut == "ouvert").count()

    return {
        "ongoing": {"valeur": ongoing, "delta_pct": None},
        "in_order": {"valeur": in_order, "delta_pct": None},
        "completed": {
            "valeur": len(completed_today),
            "delta_pct": _delta_pct(len(completed_today), len(completed_hier)),
        },
        "revenue": {
            "valeur": round(revenue_today, 2),
            "delta_pct": _delta_pct(revenue_today, revenue_hier),
        },
    }


@router.get("/wash-details")
def wash_details(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site), limit: int = 12) -> list[dict]:
    """Tableau « Wash Details » : lavages du jour (véhicule, catégorie, baie,
    statut ontime/delayed, montant)."""
    bay_ids = _bay_ids_du_site(db, site_id)
    debut = datetime.combine(date.today(), time.min)

    stmt = (
        select(Transaction)
        .where(Transaction.heure_entree >= debut)
        .order_by(Transaction.heure_entree.desc())
        .limit(limit)
    )
    if bay_ids is not None:
        stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
    txns = db.scalars(stmt).all()

    forfaits = {f.id: f for f in db.scalars(select(Forfait)).all()}
    bays = {b.id: b.numero for b in db.scalars(select(Bay)).all()}

    lignes = []
    for t in txns:
        forfait = forfaits.get(t.forfait_id)
        # Statut ontime/delayed : dépassement du temps max du forfait.
        statut = StatutLavage.ONTIME.value
        if forfait and t.duree_totale and t.duree_totale / 60 > forfait.temps_max:
            statut = StatutLavage.DELAYED.value
        lignes.append({
            "transaction_id": t.id,
            "vehicule": t.vehicule.plaque if t.vehicule else t.track_id,
            "categorie": forfait.nom if forfait else t.forfait_detecte,
            "bay": bays.get(t.bay_id),
            "statut": statut,
            "montant": float(forfait.prix) if forfait else None,
        })
    return lignes


@router.get("/graphiques")
def donnees_graphiques(db: Session = Depends(get_db)) -> dict:
    """Séries prêtes pour les graphiques : volume horaire, répartition des
    forfaits (jour) et tendance sur 7 jours (véhicules + CA)."""
    debut_jour = datetime.combine(date.today(), time.min)
    fin_jour = debut_jour + timedelta(days=1)
    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}

    # Transactions du jour (clôturées)
    txns_jour = db.scalars(
        select(Transaction).where(
            Transaction.statut == "cloturee",
            Transaction.heure_sortie >= debut_jour,
            Transaction.heure_sortie < fin_jour,
        )
    ).all()

    # Volume par heure (0-23)
    heures = Counter(t.heure_entree.hour for t in txns_jour if t.heure_entree)
    volume_horaire = [{"heure": f"{h:02d}h", "vehicules": heures.get(h, 0)} for h in range(7, 22)]

    # Répartition des forfaits (jour)
    rep = Counter(t.forfait_detecte for t in txns_jour if t.forfait_detecte)
    repartition_forfaits = [{"forfait": k, "valeur": v} for k, v in rep.items()]

    # Tendance sur 7 jours
    tendance = []
    for d in range(6, -1, -1):
        jour = date.today() - timedelta(days=d)
        db0 = datetime.combine(jour, time.min)
        df = db0 + timedelta(days=1)
        txns = db.scalars(
            select(Transaction).where(
                Transaction.statut == "cloturee",
                Transaction.heure_sortie >= db0,
                Transaction.heure_sortie < df,
            )
        ).all()
        ca = sum(prix.get(t.forfait_id, 0.0) for t in txns if t.forfait_id)
        tendance.append({
            "date": jour.strftime("%d/%m"),
            "vehicules": len(txns),
            "ca": round(ca, 2),
        })

    return {
        "volume_horaire": volume_horaire,
        "repartition_forfaits": repartition_forfaits,
        "tendance": tendance,
    }
