"""Modèles ORM. L'import ici garantit qu'Alembic/Base les découvre tous."""
from app.models.anomalie import Anomalie
from app.models.audit import JournalAudit
from app.models.bay import Bay
from app.models.camera import Camera
from app.models.cloture import ClotureCaisse
from app.models.employe import Employe
from app.models.evenement_traite import EvenementTraite
from app.models.enums import (
    AnomalieSeverite,
    AnomalieType,
    BayStatut,
    ForfaitNom,
    StatutLavage,
    ZoneCode,
)
from app.models.forfait import Forfait
from app.models.forfait_produit import ForfaitProduit
from app.models.horaire import HoraireEmploye, HoraireSite
from app.models.notification import Notification
from app.models.objectif import Objectif
from app.models.parametre import Parametre
from app.models.pointage import Pointage
from app.models.produit import Produit
from app.models.rapport import RapportJournalier
from app.models.site import Site
from app.models.ticket import Ticket
from app.models.transaction import Transaction
from app.models.utilisateur import Utilisateur
from app.models.vehicule import Vehicule

__all__ = [
    "Anomalie",
    "Bay",
    "Camera",
    "JournalAudit",
    "ClotureCaisse",
    "Employe",
    "EvenementTraite",
    "Forfait",
    "ForfaitProduit",
    "HoraireEmploye",
    "HoraireSite",
    "Notification",
    "Objectif",
    "Parametre",
    "Pointage",
    "Produit",
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
