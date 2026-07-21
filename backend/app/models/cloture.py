"""Table `clotures_caisse` — clôture de caisse journalière (rapport Z).

En fin de journée, le gérant clôture la caisse d'un site : on fige le total
théorique encaissé (somme des tickets non annulés du jour, ventilée par mode
de paiement), le gérant saisit le montant réellement compté en espèces, et le
système calcule l'écart de caisse. La clôture est archivée (PDF) et fait office
de rapport Z : une seule par (jour, site).
"""
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClotureCaisse(Base):
    __tablename__ = "clotures_caisse"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    jour: Mapped[date] = mapped_column(Date, index=True)

    nb_tickets: Mapped[int] = mapped_column(default=0)
    total_theorique: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    # Ventilation par mode : {"espece": {"nb": n, "total": x}, "carte": {...}}
    detail_modes: Mapped[dict] = mapped_column(JSON, default=dict)

    fond_caisse: Mapped[float] = mapped_column(Numeric(10, 2), default=0)  # fond de départ
    montant_compte: Mapped[float] = mapped_column(Numeric(10, 2), default=0)  # espèces comptées
    ecart: Mapped[float] = mapped_column(Numeric(10, 2), default=0)  # compté − (fond + espèces)

    notes: Mapped[str | None] = mapped_column(String(512))
    cloture_par_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateurs.id"))
    cloture_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fichier_pdf: Mapped[str | None] = mapped_column(String(256))
