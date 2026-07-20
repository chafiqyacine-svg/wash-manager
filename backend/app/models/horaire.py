"""Horaires : ouverture des sites et créneaux de travail des employés.

`jour` : 0 = lundi … 6 = dimanche. Un enregistrement par jour (et par créneau
pour les employés). Sert à mesurer présence/ponctualité et à détecter les
lavages hors horaires.
"""
from datetime import time

from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HoraireSite(Base):
    """Horaire d'ouverture d'un site pour un jour de la semaine."""
    __tablename__ = "horaires_site"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    jour: Mapped[int] = mapped_column(Integer)  # 0=lundi … 6=dimanche
    heure_ouverture: Mapped[time] = mapped_column(Time)
    heure_fermeture: Mapped[time] = mapped_column(Time)


class HoraireEmploye(Base):
    """Créneau de travail d'un employé pour un jour de la semaine."""
    __tablename__ = "horaires_employe"

    id: Mapped[int] = mapped_column(primary_key=True)
    employe_id: Mapped[int] = mapped_column(ForeignKey("employes.id"), index=True)
    jour: Mapped[int] = mapped_column(Integer)  # 0=lundi … 6=dimanche
    debut: Mapped[time] = mapped_column(Time)
    fin: Mapped[time] = mapped_column(Time)
