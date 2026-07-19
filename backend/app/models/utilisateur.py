"""Table `utilisateurs` — comptes d'accès au dashboard (manager, admin)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(128))
    hashed_password: Mapped[str] = mapped_column(String(255))
    # admin : tout ; manager : son site ; caissier : caisse/queue de son site.
    role: Mapped[str] = mapped_column(String(32), default="manager")
    # Site de rattachement (NULL = tous les sites, réservé aux admins).
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
