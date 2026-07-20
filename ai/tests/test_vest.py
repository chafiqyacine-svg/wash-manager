"""Tests de la reconnaissance de gilet (matching de couleur, pur)."""
from pipeline.vest import hex_vers_rgb, plus_proche_employe, rgb_vers_hex

PALETTE = {1: "#E11D48", 2: "#2563EB", 3: "#059669"}  # rouge, bleu, vert


def test_hex_rgb_aller_retour():
    assert hex_vers_rgb("#E11D48") == (225, 29, 72)
    assert rgb_vers_hex((225, 29, 72)) == "#E11D48"


def test_match_couleur_proche():
    # Un rouge légèrement différent -> employé 1.
    assert plus_proche_employe((220, 35, 70), PALETTE) == 1
    # Un bleu -> employé 2.
    assert plus_proche_employe((40, 100, 230), PALETTE) == 2


def test_pas_de_match_si_trop_loin():
    # Gris neutre, loin de toutes les couleurs vives -> None (seuil).
    assert plus_proche_employe((128, 128, 128), PALETTE, seuil=6000) is None


def test_palette_vide():
    assert plus_proche_employe((225, 29, 72), {}) is None
