"""Table `bays` — baies / stations de lavage au sein d'un site.

Chaque baie a un état (opérationnelle / hors service) et un effectif. Les
transactions y sont rattachées, ce qui alimente le panneau « Wash Bay Stations »
du dashboard (lavage en cours, file d'attente, temps moyen, staff).
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BayStatut


class Bay(Base):
    __tablename__ = "bays"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # « Bay Area : N »
    statut: Mapped[str] = mapped_column(String(20), default=BayStatut.OPERATIONNELLE.value)
    staff: Mapped[int] = mapped_column(Integer, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped["Site"] = relationship(back_populates="bays")  # noqa: F821
