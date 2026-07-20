"""Initialise la base : crée les tables et insère les données de référence.

Usage : `python -m app.db.seed`

Le schéma est géré par Alembic (`alembic upgrade head`). `create_all` reste ici
uniquement par commodité en dev (no-op si les tables existent déjà).
"""
from datetime import date

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Bay, Forfait, Parametre, Site, Utilisateur
from app.models.enums import BayStatut, ForfaitNom, ZoneCode
from app.services.parametres import DEFAUTS

# Sites de démonstration (multi-emplacements) et leurs baies.
SITES_DEFAUT = [
    {"nom": "Station Casablanca", "adresse": "Bd Zerktouni, Casablanca", "bays": 4},
    {"nom": "Station Rabat", "adresse": "Av. Hassan II, Rabat", "bays": 3},
]

# Forfaits par défaut (cf. tableau 7.1 du cahier des charges).
FORFAITS_DEFAUT = [
    {"nom": ForfaitNom.RAPIDE.value, "prix": 30, "temps_min": 10, "temps_max": 20,
     "zones_requises": [ZoneCode.LAVAGE_EXT.value]},
    {"nom": ForfaitNom.PREMIUM.value, "prix": 60, "temps_min": 20, "temps_max": 40,
     "zones_requises": [ZoneCode.LAVAGE_EXT.value, ZoneCode.ASPIRATION.value]},
    {"nom": ForfaitNom.COMPLET.value, "prix": 100, "temps_min": 35, "temps_max": 55,
     "zones_requises": [ZoneCode.LAVAGE_EXT.value, ZoneCode.ASPIRATION.value,
                        ZoneCode.POLISH.value]},
]


def seed() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        # Forfaits
        for f in FORFAITS_DEFAUT:
            exists = db.scalar(select(Forfait).where(Forfait.nom == f["nom"]))
            if not exists:
                db.add(Forfait(**f))

        # Sites + baies (multi-emplacements) + horaires d'ouverture par défaut
        if not db.scalar(select(Site)):
            from datetime import time as _time

            from app.models import HoraireSite
            for s in SITES_DEFAUT:
                site = Site(nom=s["nom"], adresse=s["adresse"])
                db.add(site)
                db.flush()
                for n in range(1, s["bays"] + 1):
                    db.add(Bay(site_id=site.id, numero=n,
                               statut=BayStatut.OPERATIONNELLE.value, staff=3))
                # Ouvert 8h-20h du lundi (0) au samedi (5).
                for jour in range(0, 6):
                    db.add(HoraireSite(site_id=site.id, jour=jour,
                                       heure_ouverture=_time(8, 0),
                                       heure_fermeture=_time(20, 0)))
                # Inventaire de démarrage par site.
                from app.models import Produit
                for nom, unite, qte, seuil in [
                    ("Shampoing carrosserie", "L", 40, 10),
                    ("Cire", "L", 8, 5),
                    ("Produit vitres", "L", 15, 5),
                    ("Microfibres", "unité", 60, 20),
                ]:
                    db.add(Produit(site_id=site.id, nom=nom, unite=unite,
                                   quantite=qte, seuil_alerte=seuil))

        # Paramètres configurables (valeurs par défaut)
        for cle, (valeur, description) in DEFAUTS.items():
            if not db.get(Parametre, cle):
                db.add(Parametre(cle=cle, valeur=valeur, description=description))

        # Compte manager par défaut (à changer immédiatement !)
        if not db.scalar(select(Utilisateur).where(Utilisateur.email == "admin@wash.local")):
            db.add(Utilisateur(
                email="admin@wash.local",
                nom="Administrateur",
                hashed_password=hash_password("changeme"),
                role="admin",
            ))

        db.commit()
        print("Seed terminé : forfaits + compte admin par défaut.")
        print("  ⚠️  Identifiants : admin@wash.local / changeme (à changer)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
