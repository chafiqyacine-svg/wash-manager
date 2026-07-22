"""Simulateur de station — « fausse caméra » pour le développement et la démo.

Génère des véhicules réalistes qui traversent le site et envoie les événements
au backend (comme le ferait le vrai pipeline), y compris des anomalies volontaires.
Crée aussi les tickets de caisse correspondants via l'API pour tester le
rapprochement. Ne nécessite AUCUNE caméra.

Usage :
    python simulator.py --count 30
    python simulator.py --count 50 --anomaly-rate 0.25 --backend http://localhost:8000

Prérequis : le backend tourne et la base est seedée (forfaits + compte admin).
"""
from __future__ import annotations

import argparse
import random
import string
from datetime import datetime, timedelta, timezone

import httpx

from pipeline.events import Event, EventClient, EventType

# Zones requises par forfait (miroir de la logique backend).
FORFAIT_ZONES = {
    "Rapide": ["B"],
    "Premium": ["B", "C"],
    "Complet": ["B", "C", "D"],
}
# Durée typique (minutes) passée dans chaque zone.
DUREE_ZONE_MIN = {"B": (6, 10), "C": (5, 9), "D": (8, 14)}
LETTRES_PLAQUE = "ABDHWJ" + "أبجدهـ"  # latin + quelques lettres arabes


def plaque_marocaine() -> str:
    """Génère une plaque au format marocain : chiffres-lettre-chiffres."""
    return (
        f"{random.randint(1, 99999)}-"
        f"{random.choice(LETTRES_PLAQUE)}-"
        f"{random.randint(1, 99)}"
    )


class BackendSession:
    """Petit client API pour créer des tickets (auth JWT)."""

    def __init__(self, api_base: str, email: str, password: str) -> None:
        self.api_base = api_base.rstrip("/")
        self._client = httpx.Client(timeout=10)
        self._token = self._login(email, password)

    def _login(self, email: str, password: str) -> str:
        resp = self._client.post(
            f"{self.api_base}/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def forfaits(self) -> list[dict]:
        resp = self._client.get(
            f"{self.api_base}/api/v1/forfaits",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        resp.raise_for_status()
        return resp.json()

    def couleurs_gilets(self) -> list[str]:
        """Couleurs de gilet des employés (pour simuler l'identification)."""
        resp = self._client.get(
            f"{self.api_base}/api/v1/employes",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        resp.raise_for_status()
        return [e["couleur_gilet"] for e in resp.json() if e.get("couleur_gilet")]

    def creer_ticket(self, forfait_id: int, plaque: str | None,
                     mode_paiement: str = "espece") -> None:
        self._client.post(
            f"{self.api_base}/api/v1/tickets",
            headers={"Authorization": f"Bearer {self._token}"},
            json={"forfait_id": forfait_id, "plaque": plaque,
                  "mode_paiement": mode_paiement},
        )


def simuler_vehicule(
    events: EventClient,
    session: BackendSession,
    forfaits_par_nom: dict[str, dict],
    t0: datetime,
    anomaly_rate: float,
    gilets: list[str] | None = None,
) -> None:
    """Simule un passage complet : ticket (parfois) + parcours + événements."""
    track_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    plaque = plaque_marocaine()

    forfait_paye = random.choices(["Rapide", "Premium", "Complet"], weights=[5, 3, 2])[0]
    forfait_effectue = forfait_paye
    scenario = "normal"

    r = random.random()
    if r < anomaly_rate * 0.4:
        # Forfait non respecté : payé plus que fait.
        scenario = "sous_traite"
        forfait_effectue = "Rapide" if forfait_paye != "Rapide" else "Rapide"
    elif r < anomaly_rate * 0.7:
        # Lavage non facturé : pas de ticket.
        scenario = "sans_ticket"
    elif r < anomaly_rate:
        # Ticket fantôme : ticket créé mais aucun véhicule (on émet le ticket seul).
        scenario = "ticket_fantome"

    # 1) Ticket de caisse (sauf scénario "sans_ticket")
    if scenario != "sans_ticket":
        f = forfaits_par_nom[forfait_paye]
        # Mode de paiement réaliste (majorité espèces) → alimente la clôture de caisse.
        mode = random.choices(["espece", "carte", "autre"], weights=[6, 3, 1])[0]
        # Pour le ticket fantôme, plaque volontairement absente et pas de véhicule.
        session.creer_ticket(f["id"], None if scenario == "ticket_fantome" else plaque, mode)
    if scenario == "ticket_fantome":
        return  # aucun événement véhicule

    # 2) Parcours véhicule → événements horodatés
    t = t0
    events.send(Event(EventType.ENTREE, track_id, timestamp=t.isoformat(), camera_id="cam_entree"))
    events.send(Event(EventType.PLAQUE, track_id, timestamp=t.isoformat(),
                      camera_id="cam_entree", plaque=plaque, plaque_confiance=0.95))
    # Identification du laveur par gilet (si des employés ont une couleur).
    if gilets:
        events.send(Event(EventType.BADGE, track_id, timestamp=t.isoformat(),
                          couleur_gilet=random.choice(gilets)))

    for zone in FORFAIT_ZONES[forfait_effectue]:
        t += timedelta(seconds=random.randint(20, 60))
        events.send(Event(EventType.ZONE_ENTER, track_id, timestamp=t.isoformat(), zone=zone))
        lo, hi = DUREE_ZONE_MIN[zone]
        t += timedelta(minutes=random.uniform(lo, hi))
        events.send(Event(EventType.ZONE_EXIT, track_id, timestamp=t.isoformat(), zone=zone))

    t += timedelta(seconds=random.randint(20, 60))
    events.send(Event(EventType.SORTIE, track_id, timestamp=t.isoformat(), camera_id="cam_sortie"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulateur de station de lavage")
    parser.add_argument("--backend", default="http://localhost:8000", help="URL du backend")
    parser.add_argument("--count", type=int, default=20, help="Nombre de véhicules")
    parser.add_argument("--anomaly-rate", type=float, default=0.2, help="Taux d'anomalies (0-1)")
    parser.add_argument("--ingest-key", default="change-me-ingest-key", help="Clé X-AI-Key")
    parser.add_argument("--email", default="admin@wash.local")
    parser.add_argument("--password", default="changeme")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    events = EventClient(f"{args.backend}/api/v1/events", args.ingest_key)
    session = BackendSession(args.backend, args.email, args.password)
    forfaits_par_nom = {f["nom"]: f for f in session.forfaits()}
    if not forfaits_par_nom:
        raise SystemExit("Aucun forfait en base — lancez d'abord `python -m app.db.seed`.")
    gilets = session.couleurs_gilets()  # pour simuler l'identification employé

    # Étale les arrivées sur la journée écoulée.
    debut = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
    for i in range(args.count):
        t0 = debut + timedelta(minutes=i * random.randint(8, 20))
        simuler_vehicule(events, session, forfaits_par_nom, t0, args.anomaly_rate, gilets)

    print(f"{args.count} véhicule(s) simulé(s) vers {args.backend}. "
          f"Consultez le dashboard / les rapports.")


if __name__ == "__main__":
    main()
