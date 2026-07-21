"""Table `produits` — inventaire des consommables par site.

Stock de shampoing, cire, etc., avec seuil d'alerte de réapprovisionnement.
Un produit appartient à un site (stock local à chaque emplacement).
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Produit(Base):
    __tablename__ = "produits"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    nom: Mapped[str] = mapped_column(String(128))
    unite: Mapped[str] = mapped_column(String(16), default="unité")  # L, kg, unité…
    quantite: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    seuil_alerte: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(10, 2), default=0)  # coût d'achat / unité
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
