"""Table `transactions` — un passage complet d'un véhicule sur le site.

C'est l'entité centrale : elle agrège le parcours du véhicule (temps par zone),
le forfait payé (POS) vs le forfait détecté (IA), la conformité et l'anomalie
éventuelle. Les colonnes zone_* sont alimentées par le service d'ingestion à
partir des événements du pipeline IA.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    vehicule_id: Mapped[int | None] = mapped_column(ForeignKey("vehicules.id"))
    employe_id: Mapped[int | None] = mapped_column(ForeignKey("employes.id"))
    forfait_id: Mapped[int | None] = mapped_column(ForeignKey("forfaits.id"))

    # Identifiant de suivi (track_id) attribué par le tracker du pipeline IA.
    # Sert à rapprocher les événements successifs d'un même véhicule.
    track_id: Mapped[str | None] = mapped_column(String(64), index=True)

    # Chronométrage global
    heure_entree: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heure_sortie: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duree_totale: Mapped[int | None] = mapped_column(Integer)  # secondes

    # Temps par zone (secondes). debut/fin en timestamp, duree en secondes.
    zone_b_debut: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_b_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_b_duree: Mapped[int | None] = mapped_column(Integer)
    zone_c_debut: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_c_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_c_duree: Mapped[int | None] = mapped_column(Integer)
    zone_d_debut: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_d_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone_d_duree: Mapped[int | None] = mapped_column(Integer)

    # Résultat de la classification (nom du forfait déduit du parcours réel)
    forfait_detecte: Mapped[str | None] = mapped_column(String(32))
    conforme: Mapped[bool | None] = mapped_column(Boolean)

    # Photos (chemins/urls dans le stockage médias)
    photo_entree: Mapped[str | None] = mapped_column(String(512))
    photo_sortie: Mapped[str | None] = mapped_column(String(512))

    # État de la transaction : "en_cours" tant que le véhicule est sur site,
    # "cloturee" après franchissement de la ligne de sortie.
    statut: Mapped[str] = mapped_column(String(16), default="en_cours", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vehicule: Mapped["Vehicule | None"] = relationship(back_populates="transactions")  # noqa: F821
    employe: Mapped["Employe | None"] = relationship(back_populates="transactions")  # noqa: F821
    forfait: Mapped["Forfait | None"] = relationship(back_populates="transactions")  # noqa: F821
    anomalies: Mapped[list["Anomalie"]] = relationship(  # noqa: F821
        back_populates="transaction", cascade="all, delete-orphan"
    )
