"""Notifications temps réel (WhatsApp Business API).

Les anomalies CRITIQUE/HAUTE déclenchent une alerte immédiate au(x) manager(s)
avec photo + détails. Les sévérités MOYENNE/BASSE sont agrégées dans le rapport
journalier (voir services/rapport.py).

SQUELETTE : la signature et l'aiguillage sont posés ; l'appel HTTP réel à
l'API WhatsApp est à implémenter.
"""
import httpx

from app.core.config import settings
from app.models.enums import AnomalieSeverite

_SEVERITES_ALERTE_IMMEDIATE = {AnomalieSeverite.CRITIQUE, AnomalieSeverite.HAUTE}


def doit_alerter(severite: AnomalieSeverite) -> bool:
    return severite in _SEVERITES_ALERTE_IMMEDIATE


async def envoyer_alerte_whatsapp(message: str, photo_url: str | None = None) -> bool:
    """Envoie une alerte aux numéros managers configurés. Retourne True si OK."""
    if not settings.whatsapp_api_url or not settings.manager_numbers:
        # Non configuré (dev) : on ne bloque pas le flux.
        return False

    async with httpx.AsyncClient(timeout=10) as client:
        for numero in settings.manager_numbers:
            # TODO(dev): adapter au format exact de votre fournisseur WhatsApp
            #   (Meta Cloud API, Twilio, 360dialog…). Gérer templates & médias.
            payload = {
                "to": numero,
                "type": "text",
                "text": {"body": message},
            }
            headers = {"Authorization": f"Bearer {settings.whatsapp_api_token}"}
            try:
                resp = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
                resp.raise_for_status()
            except httpx.HTTPError:
                # TODO(dev): journaliser l'échec et prévoir une file de retry.
                return False
    return True
