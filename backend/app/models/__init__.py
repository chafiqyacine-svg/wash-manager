"""Modèles ORM. L'import ici garantit qu'Alembic/Base les découvre tous."""
from app.models.anomalie import Anomalie
from app.models.employe import Employe
from app.models.enums import AnomalieSeverite, AnomalieType, ForfaitNom, ZoneCode
from app.models.forfait import Forfait
from app.models.rapport import RapportJournalier
from app.models.ticket import Ticket
from app.models.transaction import Transaction
from app.models.utilisateur import Utilisateur
from app.models.vehicule import Vehicule

__all__ = [
    "Anomalie",
    "Employe",
    "Forfait",
    "RapportJournalier",
    "Ticket",
    "Transaction",
    "Utilisateur",
    "Vehicule",
    "AnomalieSeverite",
    "AnomalieType",
    "ForfaitNom",
    "ZoneCode",
]
