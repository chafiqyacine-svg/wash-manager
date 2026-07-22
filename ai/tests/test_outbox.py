"""Tests de la file locale durable (outbox) et de l'envoi durable/ordonné."""
from pipeline.events import Event, EventClient, EventType
from pipeline.outbox import Outbox


# ─── Outbox (persistance pure) ───────────────────────────────────────────────
def test_outbox_fifo_et_suppression():
    ob = Outbox(":memory:")
    a = ob.ajouter({"type": "entree", "track_id": "v1"})
    b = ob.ajouter({"type": "sortie", "track_id": "v1"})
    assert ob.taille() == 2
    attente = ob.en_attente()
    assert [i for i, _ in attente] == [a, b]                 # ordre d'insertion
    assert attente[0][1]["type"] == "entree"
    ob.supprimer(a)
    assert ob.taille() == 1 and ob.en_attente()[0][0] == b


def test_outbox_persiste_sur_disque(tmp_path):
    chemin = str(tmp_path / "outbox.db")
    ob = Outbox(chemin); ob.ajouter({"type": "entree", "track_id": "v1"}); ob.fermer()
    # Réouverture : l'événement est toujours là.
    ob2 = Outbox(chemin)
    assert ob2.taille() == 1


# ─── EventClient durable (avec outbox) ───────────────────────────────────────
class _Reseau:
    """Faux transport : `up` contrôle la disponibilité réseau."""
    def __init__(self, up=True):
        self.up = up
        self.recus = []

    def post(self, url, json=None, headers=None):
        if not self.up:
            import httpx
            raise httpx.ConnectError("réseau coupé")
        self.recus.append(json)
        return _Resp()


class _Resp:
    def raise_for_status(self):
        return None


def _client(reseau, outbox):
    c = EventClient("http://backend/api/v1/events", "k", outbox=outbox)
    c._client = reseau
    return c


def test_envoi_persiste_puis_draine_a_la_reprise():
    ob = Outbox(":memory:")
    reseau = _Reseau(up=False)
    client = _client(reseau, ob)

    # Réseau coupé : les événements sont persistés, rien n'est perdu.
    client.send(Event(EventType.ENTREE, "v1"))
    client.send(Event(EventType.SORTIE, "v1"))
    assert ob.taille() == 2 and reseau.recus == []

    # Réseau rétabli : le prochain send draine toute la file, dans l'ordre.
    reseau.up = True
    client.send(Event(EventType.PLAQUE, "v1", plaque="12345-A-67"))
    assert ob.taille() == 0
    types = [p["type"] for p in reseau.recus]
    assert types == ["entree", "sortie", "plaque"]           # FIFO préservé


def test_flush_s_arrete_au_premier_echec():
    ob = Outbox(":memory:")
    ob.ajouter({"type": "entree", "track_id": "v1"})
    ob.ajouter({"type": "sortie", "track_id": "v1"})
    reseau = _Reseau(up=False)
    client = _client(reseau, ob)
    assert client.flush() == 0        # réseau coupé -> rien envoyé
    assert ob.taille() == 2           # tout est conservé


def test_sans_outbox_comportement_direct():
    reseau = _Reseau(up=True)
    client = _client(reseau, outbox=None)
    assert client.send(Event(EventType.ENTREE, "v1")) is True
    assert len(reseau.recus) == 1
