"""Jeu de données de DÉMONSTRATION (sans caméras ni vraies données).

Peuple la base sur plusieurs jours : employés, véhicules, transactions
clôturées (avec temps par zone, forfait détecté, conformité), tickets rapprochés
et anomalies. Permet de voir le dashboard et les rapports « vivre » immédiatement.

Usage : python -m app.db.demo [nb_jours] [vehicules_par_jour]
        python -m app.db.demo 7 25

⚠️ Données factices — à ne pas lancer en production.
"""
import random
import string
import sys
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import Bay, Employe, Forfait, Ticket, Transaction, Vehicule
from app.services.ingestion import finaliser_transaction

EMPLOYES = ["Youssef", "Karim", "Rachid", "Hamza"]
FORFAIT_ZONES = {"Rapide": ["B"], "Premium": ["B", "C"], "Complet": ["B", "C", "D"]}
LETTRES = "ABDHWJ"


def _plaque() -> str:
    return f"{random.randint(1, 99999)}-{random.choice(LETTRES)}-{random.randint(1, 99)}"


def _track() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def generer(nb_jours: int = 7, par_jour: int = 25) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        forfaits = {f.nom: f for f in db.scalars(select(Forfait)).all()}
        if not forfaits:
            raise SystemExit("Lancez d'abord `python -m app.db.seed` (forfaits manquants).")

        employes = _assurer_employes(db)
        bays = db.scalars(select(Bay)).all()  # peut être vide si seed sans sites

        for d in range(nb_jours):
            jour = date.today() - timedelta(days=d)
            for i in range(par_jour):
                _generer_transaction(db, jour, i, forfaits, employes, bays)

        # Quelques lavages EN COURS aujourd'hui (peuplent « ongoing » + stations).
        if bays:
            _generer_en_cours(db, forfaits, employes, bays, nb=min(len(bays), 5))

        db.commit()
        print(f"Démo générée : {nb_jours} jour(s) × ~{par_jour} véhicules "
              f"+ {min(len(bays), 5) if bays else 0} en cours.")
    finally:
        db.close()


def _assurer_employes(db) -> list[Employe]:
    existants = db.scalars(select(Employe)).all()
    if existants:
        return existants
    emps = [Employe(nom=n, badge_nfc_id=f"NFC{1000+i}") for i, n in enumerate(EMPLOYES)]
    db.add_all(emps)
    db.flush()
    return emps


def _vehicule(db, plaque: str, base: datetime) -> Vehicule:
    vehicule = db.scalar(select(Vehicule).where(Vehicule.plaque == plaque))
    if vehicule is None:
        vehicule = Vehicule(plaque=plaque, premiere_visite=base,
                            derniere_visite=base, nombre_visites=1)
        db.add(vehicule)
        db.flush()
    return vehicule


def _generer_transaction(db, jour: date, i: int, forfaits: dict, employes: list,
                         bays: list) -> None:
    forfait_paye = random.choices(["Rapide", "Premium", "Complet"], weights=[5, 3, 2])[0]
    forfait_effectue = forfait_paye
    scenario = random.choices(
        ["normal", "sous_traite", "sans_ticket"], weights=[80, 12, 8]
    )[0]
    if scenario == "sous_traite" and forfait_paye != "Rapide":
        forfait_effectue = "Rapide"

    # Horodatage : réparti sur la journée (8h → 20h).
    base = datetime.combine(jour, time(8, 0), tzinfo=timezone.utc) + timedelta(minutes=i * 25)
    plaque = _plaque()
    vehicule = _vehicule(db, plaque, base)

    # Transaction + temps par zone
    txn = Transaction(
        track_id=_track(), vehicule_id=vehicule.id,
        employe_id=random.choice(employes).id,
        bay_id=random.choice(bays).id if bays else None,
        heure_entree=base, statut="cloturee",
    )
    t = base
    for zone in FORFAIT_ZONES[forfait_effectue]:
        t += timedelta(seconds=random.randint(30, 90))
        debut = t
        t += timedelta(minutes=random.randint(5, 13))
        prefix = {"B": "zone_b", "C": "zone_c", "D": "zone_d"}[zone]
        setattr(txn, f"{prefix}_debut", debut)
        setattr(txn, f"{prefix}_fin", t)
        setattr(txn, f"{prefix}_duree", int((t - debut).total_seconds()))
    t += timedelta(seconds=random.randint(30, 90))
    txn.heure_sortie = t
    txn.duree_totale = int((t - base).total_seconds())
    db.add(txn)
    db.flush()

    # Ticket (sauf scénario sans_ticket) — puis finalisation (classe + anomalies)
    ticket = None
    if scenario != "sans_ticket":
        f = forfaits[forfait_paye]
        ticket = Ticket(forfait_id=f.id, prix=f.prix, plaque=plaque, heure=base, statut="ouvert")
        db.add(ticket)
        db.flush()

    finaliser_transaction(db, txn, ticket)


def _generer_en_cours(db, forfaits: dict, employes: list, bays: list, nb: int) -> None:
    """Lavages en cours (une baie chacun) pour peupler le temps réel."""
    maintenant = datetime.now(timezone.utc)
    for bay in random.sample(bays, nb):
        forfait_nom = random.choice(list(forfaits))
        base = maintenant - timedelta(minutes=random.randint(3, 15))
        plaque = _plaque()
        vehicule = _vehicule(db, plaque, base)
        txn = Transaction(
            track_id=_track(), vehicule_id=vehicule.id,
            employe_id=random.choice(employes).id, bay_id=bay.id,
            forfait_id=forfaits[forfait_nom].id,
            heure_entree=base, statut="en_cours", zone_b_debut=base,
        )
        db.add(txn)


if __name__ == "__main__":
    jours = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    par_jour = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    generer(jours, par_jour)
