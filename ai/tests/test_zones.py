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


def test_ligne_hysteresis_ignore_le_bruit_pres_de_la_ligne():
    # marge = bande morte : un point pile sur la ligne ne change pas le côté.
    ligne = DetecteurLigne((0, 100), (200, 100), marge=5000)
    ligne.a_franchi("v1", (100, 40))                 # franc au-dessus (cote=-12000)
    assert ligne.a_franchi("v1", (100, 99)) is False  # quasi sur la ligne (|cote|<marge)
    assert ligne.a_franchi("v1", (100, 101)) is False # toujours dans la bande morte
    assert ligne.a_franchi("v1", (100, 160)) is True  # franc en dessous -> franchissement


def test_ligne_directionnelle():
    # sens=+1 : ne compte que le passage côté négatif -> positif.
    descend = DetecteurLigne((0, 100), (200, 100), sens=1)
    descend.a_franchi("v1", (100, 50))               # côté négatif
    assert descend.a_franchi("v1", (100, 150)) is True   # -> positif : compté
    monte = DetecteurLigne((0, 100), (200, 100), sens=1)
    monte.a_franchi("v2", (100, 150))                # côté positif
    assert monte.a_franchi("v2", (100, 50)) is False     # -> négatif : ignoré (mauvais sens)


def test_zone_anti_rebond():
    # 2 confirmations requises : un passage d'une seule frame est ignoré.
    zone = DetecteurZone([(0, 0), (10, 0), (10, 10), (0, 10)], confirmations=2)
    assert zone.maj("v1", (5, 5)) is None    # 1re frame dedans : pas encore confirmé
    assert zone.maj("v1", (5, 5)) == "enter"  # 2e frame consécutive : confirmé
    assert zone.maj("v1", (50, 50)) is None   # 1re frame dehors : pas encore
    assert zone.maj("v1", (50, 50)) == "exit" # 2e frame : confirmé


def test_zone_rebond_annule_avant_confirmation():
    zone = DetecteurZone([(0, 0), (10, 0), (10, 10), (0, 10)], confirmations=3)
    assert zone.maj("v1", (5, 5)) is None     # candidat "dedans" (1)
    assert zone.maj("v1", (50, 50)) is None   # revient dehors avant confirmation -> annulé
    # Toujours aucun enter émis (le clignotement a été filtré).
    assert zone.maj("v1", (5, 5)) is None     # recommence à compter (1)


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
