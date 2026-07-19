"""LPR — lecture des plaques marocaines.

Pipeline (cf. section 6) : détection plaque → crop → prétraitement → OCR →
validation format marocain → association. La regex de validation est fournie ;
l'OCR et le prétraitement sont à brancher.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Format marocain : chiffres - lettre(s) arabe(s) - chiffres (ex: 12345-A-67).
# En pratique l'OCR peut retourner la translittération latine de la lettre.
# TODO(dev): affiner selon la sortie réelle de votre modèle OCR (arabe vs latin).
REGEX_PLAQUE_MA = re.compile(r"^\d{1,6}[\-\s]?[A-Za-z؀-ۿ]{1,2}[\-\s]?\d{1,2}$")


@dataclass
class ResultatLPR:
    plaque: str | None
    confiance: float
    valide: bool


def valider_plaque(texte: str) -> bool:
    return bool(REGEX_PLAQUE_MA.match(texte.strip()))


class LecteurPlaque:
    def __init__(self, plaque_detector, ocr_lang: list[str]) -> None:
        self.plaque_detector = plaque_detector  # instance de Detector (classe "plaque")
        self.ocr_lang = ocr_lang
        self._ocr = None

    def load(self) -> None:
        # TODO(dev):
        #   import easyocr ; self._ocr = easyocr.Reader(self.ocr_lang)
        #   (ou PaddleOCR). Charger éventuellement un modèle affiné MA.
        raise NotImplementedError("Charger le moteur OCR ici.")

    def lire(self, image) -> ResultatLPR:
        """Détecte la plaque dans l'image, l'extrait et lit les caractères."""
        # TODO(dev):
        #   1. detections = self.plaque_detector.detect(image)
        #   2. crop = découper la meilleure bbox
        #   3. prétraitement : redressement, contraste, upscale
        #   4. texte, conf = self._ocr.readtext(crop)
        #   5. valider_plaque(texte) ; si invalide -> stocker la capture
        raise NotImplementedError
