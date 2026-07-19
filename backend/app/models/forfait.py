"""Table `forfaits` — définition des formules et de leurs exigences.

`zones_requises` liste les codes de zones que le forfait DOIT couvrir
(ex: Complet = ["B", "C", "D"]). C'est la source de vérité utilisée par le
service de classification (voir services/classification.py).
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Forfait(Base):
    __tablename__ = "forfaits"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(32), unique=True)  # Rapide/Premium/Complet
    prix: Mapped[float] = mapped_column(Numeric(10, 2))
    # Liste de ZoneCode.value requis, ex: ["B", "C", "D"]
    zones_requises: Mapped[list] = mapped_column(JSON, default=list)
    temps_min: Mapped[int] = mapped_column(Integer)  # minutes
    temps_max: Mapped[int] = mapped_column(Integer)  # minutes

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="forfait"
    )
