"""Tests de la supervision caméra côté edge (heartbeat + service périodique)."""
import threading

from pipeline.events import EventClient, Heartbeat


class _Resp:
    def __init__(self, boom=False):
        self._boom = boom

    def raise_for_status(self):
        if self._boom:
            import httpx
            raise httpx.HTTPError("boom")


class _FakeHttp:
    def __init__(self, boom=False):
        self._boom = boom
        self.posts = []

    def post(self, url, json=None, headers=None):
        self.posts.append((url, json))
        return _Resp(self._boom)


def _client(boom=False):
    c = EventClient("http://backend/api/v1/events", "k")
    c._client = _FakeHttp(boom)
    return c


def test_heartbeat_poste_sur_le_bon_endpoint():
    client = _client()
    assert client.heartbeat({"camera_id": "cam1"}) is True
    url, payload = client._client.posts[0]
    assert url.endswith("/events/heartbeat")
    assert payload["camera_id"] == "cam1"


def test_heartbeat_echec_reseau_renvoie_false():
    client = _client(boom=True)
    assert client.heartbeat({"camera_id": "cam1"}) is False


def test_service_tick_envoie_un_par_camera():
    client = _client()
    hb = Heartbeat(client, source=lambda: [{"camera_id": "a"}, {"camera_id": "b"}])
    assert hb._tick() == 2
    cams = [p["camera_id"] for _, p in client._client.posts]
    assert cams == ["a", "b"]


def test_service_periodique_en_tache_de_fond():
    client = _client()
    appelle = threading.Event()

    def source():
        appelle.set()
        return [{"camera_id": "a"}]

    hb = Heartbeat(client, source=source, intervalle=0.01)
    hb.demarrer()          # 1er tick immédiat
    try:
        assert appelle.wait(timeout=2)
        assert any(p["camera_id"] == "a" for _, p in client._client.posts)
    finally:
        hb.arreter()


def test_source_qui_leve_ne_tue_pas_le_service():
    client = _client()
    def source():
        raise RuntimeError("boom")
    hb = Heartbeat(client, source=source)
    assert hb._tick() == 0   # exception absorbée
