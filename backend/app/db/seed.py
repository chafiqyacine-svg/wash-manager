"""Initialise la base : crée les tables et insère les données de référence.

Usage : `python -m app.db.seed`

⚠️ Utilise create_all pour le prototypage. En production, préférez Alembic.
TODO(dev): mettre en place les migrations Alembic et retirer create_all.
"""
from datetime import date

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Forfait, Utilisateur
from app.models.enums import ForfaitNom, ZoneCode

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
