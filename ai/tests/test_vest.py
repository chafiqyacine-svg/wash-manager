"""Tests de la reconnaissance de gilet (matching de couleur, pur)."""
from pipeline.vest import (
    bbox_la_plus_proche,
    hex_vers_rgb,
    plus_proche_employe,
    rgb_vers_hex,
    snap_couleur,
)

PALETTE = {1: "#E11D48", 2: "#2563EB", 3: "#059669"}  # rouge, bleu, vert
COULEURS_REF = ["#E11D48", "#2563EB", "#059669"]


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


def test_snap_couleur_ramene_au_hex_canonique():
    # Un rouge mesuré bruité -> ramené EXACTEMENT à la couleur enregistrée.
    assert snap_couleur((220, 35, 70), COULEURS_REF) == "#E11D48"
    assert snap_couleur((40, 100, 230), COULEURS_REF) == "#2563EB"


def test_snap_couleur_none_si_trop_loin():
    assert snap_couleur((128, 128, 128), COULEURS_REF, seuil=6000) is None
    assert snap_couleur((0, 0, 0), []) is None


def test_bbox_la_plus_proche():
    # Deux personnes ; le point du véhicule est proche de la seconde.
    bboxes = [(0, 0, 10, 10), (90, 90, 110, 110)]
    assert bbox_la_plus_proche((100, 100), bboxes) == 1
    assert bbox_la_plus_proche((0, 0), bboxes) == 0
    assert bbox_la_plus_proche((5, 5), []) is None
