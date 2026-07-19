"""Énumérations partagées du domaine métier."""
import enum


class ZoneCode(str, enum.Enum):
    """Zones physiques du site (cf. section 5 du cahier des charges)."""
    ENTREE = "A"       # ligne virtuelle d'entrée + LPR
    LAVAGE_EXT = "B"   # lavage extérieur
    ASPIRATION = "C"   # aspiration intérieur
    POLISH = "D"       # polish / cire (finition)
    SORTIE = "E"       # ligne virtuelle de sortie


class ForfaitNom(str, enum.Enum):
    RAPIDE = "Rapide"
    PREMIUM = "Premium"
    COMPLET = "Complet"


class AnomalieType(str, enum.Enum):
    FORFAIT_NON_RESPECTE = "forfait_non_respecte"   # payé > effectué
    LAVAGE_NON_FACTURE = "lavage_non_facture"       # véhicule sans ticket POS
    TICKET_FANTOME = "ticket_fantome"               # ticket POS sans véhicule
    TEMPS_ANORMAL = "temps_anormal"                 # durée trop courte/longue
    PLAQUE_NON_LUE = "plaque_non_lue"               # échec OCR


class AnomalieSeverite(str, enum.Enum):
    CRITIQUE = "critique"
    HAUTE = "haute"
    MOYENNE = "moyenne"
    BASSE = "basse"


class BayStatut(str, enum.Enum):
    OPERATIONNELLE = "operationnelle"
    HORS_SERVICE = "hors_service"


class StatutLavage(str, enum.Enum):
    """État temporel d'un lavage (dérivé), affiché dans « Wash Details »."""
    ONTIME = "ontime"
    DELAYED = "delayed"
