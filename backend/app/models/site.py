"""Table `sites` — emplacements de lavage (multi-sites).

Un même système gère plusieurs stations physiques. Chaque site possède ses
baies, ses transactions et ses employés. Le dashboard peut filtrer par site ou
agréger tous les sites.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(128))
    adresse: Mapped[str | None] = mapped_column(String(255))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bays: Mapped[list["Bay"]] = relationship(back_populates="site")  # noqa: F821
