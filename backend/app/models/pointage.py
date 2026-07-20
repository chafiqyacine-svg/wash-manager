"""Table `pointages` — pointage des employés (arrivée/départ) avec selfie.

L'employé se prend en photo (selfie en direct) au début de son travail. Le
serveur enregistre l'HEURE EXACTE de réception (`heure`) — cette heure fait foi,
l'employé ne peut donc pas antidater son arrivée avec une ancienne photo.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Pointage(Base):
    __tablename__ = "pointages"

    id: Mapped[int] = mapped_column(primary_key=True)
    employe_id: Mapped[int] = mapped_column(ForeignKey("employes.id"), index=True)
    type: Mapped[str] = mapped_column(String(16), default="arrivee")  # arrivee | depart
    # Heure serveur (autoritaire) au moment de la réception du selfie.
    heure: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    photo: Mapped[str | None] = mapped_column(String(512))

    employe: Mapped["Employe"] = relationship()  # noqa: F821
