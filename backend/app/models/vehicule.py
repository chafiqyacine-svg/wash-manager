"""Table `vehicules` — un enregistrement par plaque connue."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vehicule(Base):
    __tablename__ = "vehicules"

    id: Mapped[int] = mapped_column(primary_key=True)
    plaque: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    premiere_visite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    derniere_visite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nombre_visites: Mapped[int] = mapped_column(Integer, default=0)
    photo_reference: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="vehicule"
    )
