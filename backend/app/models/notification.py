"""Table `notifications` — alertes envoyées (WhatsApp/email) + leur historique.

Chaque alerte déclenchée (anomalie critique, écart de caisse, test…) y est
journalisée avec son canal, son destinataire et son statut d'envoi. Sert à la
fois de trace de contrôle et de file (les envois réels restent TODO(dev) : le
statut « simule » indique une alerte non encore transmise faute de canal
configuré).
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    cree_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    canal: Mapped[str] = mapped_column(String(16))          # whatsapp | email | log
    destinataire: Mapped[str | None] = mapped_column(String(255))
    sujet: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    severite: Mapped[str | None] = mapped_column(String(16))
    statut: Mapped[str] = mapped_column(String(16), default="simule")  # envoye|echec|simule

    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    ref_type: Mapped[str | None] = mapped_column(String(32))  # ex: "anomalie", "cloture"
    ref_id: Mapped[int | None] = mapped_column()
