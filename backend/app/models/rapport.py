"""Table `rapports_journaliers` — synthèse quotidienne archivée."""
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RapportJournalier(Base):
    __tablename__ = "rapports_journaliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    total_vehicules: Mapped[int] = mapped_column(Integer, default=0)
    total_ca: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    # {"Rapide": 12, "Premium": 8, "Complet": 5}
    repartition_forfaits: Mapped[dict] = mapped_column(JSON, default=dict)
    taux_conformite: Mapped[float] = mapped_column(Numeric(5, 2), default=0)  # pourcentage
    nombre_anomalies: Mapped[int] = mapped_column(Integer, default=0)
    # Liste des métriques par employé (voir services/rapport.py)
    performance_employes: Mapped[list] = mapped_column(JSON, default=list)
    fichier_pdf: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
