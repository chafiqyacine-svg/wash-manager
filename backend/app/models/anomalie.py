"""Table `anomalies` — écarts détectés (facturation, temps, OCR)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AnomalieSeverite, AnomalieType


class Anomalie(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))
    # Employé concerné (pour les alertes RH : retard, absence).
    employe_id: Mapped[int | None] = mapped_column(ForeignKey("employes.id"))

    type: Mapped[AnomalieType] = mapped_column(String(32))
    severite: Mapped[AnomalieSeverite] = mapped_column(String(16), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    heure: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    photo: Mapped[str | None] = mapped_column(String(512))
    notifie: Mapped[bool] = mapped_column(Boolean, default=False)  # alerte envoyée ?
    resolu: Mapped[bool] = mapped_column(Boolean, default=False)   # traité par le manager ?

    transaction: Mapped["Transaction | None"] = relationship(back_populates="anomalies")  # noqa: F821
