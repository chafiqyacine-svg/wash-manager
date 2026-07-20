"""Modèles ORM. L'import ici garantit qu'Alembic/Base les découvre tous."""
from app.models.anomalie import Anomalie
from app.models.bay import Bay
from app.models.employe import Employe
from app.models.enums import (
    AnomalieSeverite,
    AnomalieType,
    BayStatut,
    ForfaitNom,
    StatutLavage,
    ZoneCode,
)
from app.models.forfait import Forfait
from app.models.horaire import HoraireEmploye, HoraireSite
from app.models.parametre import Parametre
from app.models.rapport import RapportJournalier
from app.models.site import Site
from app.models.ticket import Ticket
from app.models.transaction import Transaction
from app.models.utilisateur import Utilisateur
from app.models.vehicule import Vehicule

__all__ = [
    "Anomalie",
    "Bay",
    "Employe",
    "Forfait",
    "HoraireEmploye",
    "HoraireSite",
    "Parametre",
    "RapportJournalier",
    "Site",
    "Ticket",
    "Transaction",
    "Utilisateur",
    "Vehicule",
    "AnomalieSeverite",
    "AnomalieType",
    "BayStatut",
    "ForfaitNom",
    "StatutLavage",
    "ZoneCode",
]
