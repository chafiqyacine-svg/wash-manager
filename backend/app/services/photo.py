"""Stockage des selfies de pointage, horodatés par le serveur.

Le fichier est enregistré sous MEDIA_ROOT/pointages/. Si Pillow est disponible,
l'heure exacte (serveur) est incrustée sur l'image (filigrane anti-fraude) — le
selfie « donne le moment exact de la prise ». Sinon, l'heure reste enregistrée en
base (autoritaire) et le fichier est stocké tel quel.
"""
import os
from datetime import datetime


def enregistrer_selfie(contenu: bytes, media_root: str, employe_id: int,
                       heure: datetime) -> str:
    """Enregistre le selfie (avec filigrane horaire si possible). Retourne le
    chemin relatif au stockage médias."""
    dossier = os.path.join(media_root, "pointages")
    os.makedirs(dossier, exist_ok=True)
    horodatage = heure.strftime("%Y%m%d_%H%M%S")
    nom = f"emp{employe_id}_{horodatage}.jpg"
    chemin_abs = os.path.join(dossier, nom)

    image_finale = _incruster_horodatage(contenu, heure)
    with open(chemin_abs, "wb") as f:
        f.write(image_finale)
    return os.path.join("pointages", nom)


def _incruster_horodatage(contenu: bytes, heure: datetime) -> bytes:
    """Incruste l'heure sur l'image via Pillow (si dispo), sinon renvoie brut."""
    try:
        import io

        from PIL import Image, ImageDraw
    except ImportError:
        return contenu  # Pillow non installé : on garde l'image brute.

    try:
        img = Image.open(io.BytesIO(contenu)).convert("RGB")
        draw = ImageDraw.Draw(img)
        texte = heure.strftime("%d/%m/%Y %H:%M:%S")
        # Bandeau + texte en bas à gauche.
        draw.rectangle([0, img.height - 28, 260, img.height], fill=(0, 0, 0))
        draw.text((6, img.height - 22), texte, fill=(255, 255, 255))
        sortie = io.BytesIO()
        img.save(sortie, format="JPEG", quality=85)
        return sortie.getvalue()
    except Exception:
        return contenu
