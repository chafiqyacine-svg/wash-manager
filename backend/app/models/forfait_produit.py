"""Table `forfait_produits` — recette de consommation d'un forfait.

Définit, pour un forfait donné, quel produit est consommé et à quel rythme :
`lavages_par_unite` = nombre de lavages qui consomment 1 unité du produit
(ex: 1 L de cire tous les 20 lavages Complet).

À chaque lavage effectué, le stock du produit (au site du lavage) est décrémenté
de 1 / lavages_par_unite.
"""
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ForfaitProduit(Base):
    __tablename__ = "forfait_produits"

    id: Mapped[int] = mapped_column(primary_key=True)
    forfait_id: Mapped[int] = mapped_column(ForeignKey("forfaits.id"), index=True)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produits.id"), index=True)
    lavages_par_unite: Mapped[int] = mapped_column(Integer, default=1)

    produit: Mapped["Produit"] = relationship()  # noqa: F821
