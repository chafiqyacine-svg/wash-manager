"""Table `tickets` — caisse intégrée (remplace un POS externe).

Tant que la station n'a pas de système de caisse, l'opérateur crée un ticket au
moment de l'encaissement (forfait payé + plaque optionnelle). Ce ticket est LA
source de vérité du « forfait payé », rapprochée ensuite de la transaction
détectée par l'IA (voir services/reconciliation.py).

Le jour où un vrai POS est installé, il suffira d'alimenter cette table via un
connecteur au lieu de la saisie manuelle — le reste du système ne change pas.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    forfait_id: Mapped[int] = mapped_column(ForeignKey("forfaits.id"))
    prix: Mapped[float] = mapped_column(Numeric(10, 2))

    # Plaque saisie en caisse (facultative) : améliore fortement le rapprochement.
    plaque: Mapped[str | None] = mapped_column(String(32), index=True)
    # Caissier / employé ayant encaissé (facultatif).
    employe_id: Mapped[int | None] = mapped_column(ForeignKey("employes.id"))
    reference: Mapped[str | None] = mapped_column(String(64))  # n° de ticket libre

    # Mode d'encaissement (espece / carte / autre) — sert à la clôture de caisse.
    mode_paiement: Mapped[str] = mapped_column(String(16), default="espece")
    # Site d'encaissement (pour la clôture par site).
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)

    heure: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ouvert -> rapproché (associé à une transaction) | annule
    statut: Mapped[str] = mapped_column(String(16), default="ouvert", index=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    forfait: Mapped["Forfait"] = relationship()  # noqa: F821
