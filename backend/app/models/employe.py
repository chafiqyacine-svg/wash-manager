"""Table `employes` — laveurs identifiés par badge NFC."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Employe(Base):
    __tablename__ = "employes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(128))
    badge_nfc_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    # Couleur de gilet (hex, ex "#E11D48") pour l'identification par vision.
    couleur_gilet: Mapped[str | None] = mapped_column(String(9))
    date_embauche: Mapped[date | None] = mapped_column(Date)
    # Emplacement d'affectation (NULL = non affecté / polyvalent).
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="employe"
    )
