"""Tests de la géométrie des zones/lignes (pur, sans dépendances lourdes)."""
from pipeline.zones import DetecteurLigne, DetecteurZone, point_dans_polygone


def test_franchissement_ligne():
    ligne = DetecteurLigne((0, 100), (200, 100))  # ligne horizontale y=100
    t = "v1"
    assert ligne.a_franchi(t, (100, 50)) is False   # 1er point : pas de référence
    assert ligne.a_franchi(t, (100, 50)) is False   # toujours au-dessus
    assert ligne.a_franchi(t, (100, 150)) is True    # traverse vers le bas


def test_point_dans_polygone():
    carre = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert point_dans_polygone((5, 5), carre) is True
    assert point_dans_polygone((15, 5), carre) is False


def test_zone_enter_exit():
    zone = DetecteurZone([(0, 0), (10, 0), (10, 10), (0, 10)])
    t = "v1"
    assert zone.maj(t, (5, 5)) == "enter"
    assert zone.maj(t, (6, 6)) is None      # reste dedans
    assert zone.maj(t, (50, 50)) == "exit"


def test_ligne_borne_la_memoire():
    ligne = DetecteurLigne((0, 100), (200, 100), max_tracks=10)
    for i in range(1000):
        ligne.a_franchi(f"v{i}", (100, 50))
    assert len(ligne._dernier_cote) <= 10


def test_zone_borne_la_memoire():
    zone = DetecteurZone([(0, 0), (10, 0), (10, 10), (0, 10)], max_tracks=10)
    for i in range(1000):
        zone.maj(f"v{i}", (5, 5))
    assert len(zone._present) <= 10
