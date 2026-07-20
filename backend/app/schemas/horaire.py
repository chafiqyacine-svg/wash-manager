"""Schémas des horaires (ouverture site + travail employé)."""
from datetime import time

from pydantic import BaseModel, ConfigDict


class HoraireSiteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    jour: int                 # 0=lundi … 6=dimanche
    heure_ouverture: time
    heure_fermeture: time


class HoraireEmployeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    jour: int
    debut: time
    fin: time
