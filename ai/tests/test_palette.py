"""Tests du chargement dynamique de la palette de gilets (edge ↔ backend)."""
from run import injecter_palette
from pipeline.events import EventClient


class _FakeResp:
    def __init__(self, payload=None, boom=False):
        self._payload = payload or {}
        self._boom = boom

    def raise_for_status(self):
        if self._boom:
            import httpx
            raise httpx.HTTPError("boom")

    def json(self):
        return self._payload


class _FakeHttp:
    def __init__(self, resp):
        self._resp = resp
        self.appels = []

    def get(self, url, headers=None, params=None):
        self.appels.append((url, params))
        return self._resp


def test_charger_palette_ok():
    client = EventClient("http://backend/api/v1/events", "k")
    client._client = _FakeHttp(_FakeResp({"couleurs": ["#E11D48", "#2563EB"]}))
    assert client.charger_palette_gilets() == ["#E11D48", "#2563EB"]
    # L'URL dérive bien de events_url.
    assert client._client.appels[0][0].endswith("/events/palette-gilets")


def test_charger_palette_echec_renvoie_liste_vide():
    client = EventClient("http://backend/api/v1/events", "k")
    client._client = _FakeHttp(_FakeResp(boom=True))
    assert client.charger_palette_gilets() == []


# ─── Injection dans les caméras ──────────────────────────────────────────────
def test_injecter_palette_remplit_les_zones():
    cams = [
        {"id": "z1", "role": "zone", "detecter_gilet": True},
        {"id": "e1", "role": "entree"},  # pas de gilet -> inchangé
    ]
    injecter_palette(cams, ["#E11D48"])
    assert cams[0]["palette_gilets"] == ["#E11D48"]
    assert "palette_gilets" not in cams[1]


def test_injecter_palette_respecte_override_config():
    cams = [{"id": "z1", "role": "zone", "detecter_gilet": True,
             "palette_gilets": ["#ABCDEF"]}]
    injecter_palette(cams, ["#E11D48"])
    assert cams[0]["palette_gilets"] == ["#ABCDEF"]  # config prioritaire
