"""File d'attente locale persistante (outbox) des événements edge → backend.

Garantit qu'AUCUN événement n'est perdu si le réseau tombe : chaque événement
est d'abord persisté localement (SQLite), puis retiré une fois acquitté par le
backend. Au retour du réseau, les événements en attente sont renvoyés **dans
l'ordre** (FIFO) pour préserver la cohérence du parcours véhicule.

stdlib pure (sqlite3 + json) : aucune dépendance supplémentaire sur l'edge.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone


class Outbox:
    """Tampon local d'événements non encore acquittés par le backend."""

    def __init__(self, path: str = ":memory:") -> None:
        # check_same_thread=False : la boucle caméra et le flush peuvent différer.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS outbox (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   payload TEXT NOT NULL,
                   cree_at TEXT NOT NULL,
                   essais INTEGER NOT NULL DEFAULT 0
               )"""
        )
        self._conn.commit()

    def ajouter(self, payload: dict) -> int:
        """Persiste un événement ; renvoie son id local."""
        cur = self._conn.execute(
            "INSERT INTO outbox (payload, cree_at) VALUES (?, ?)",
            (json.dumps(payload), datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def en_attente(self, limite: int = 100) -> list[tuple[int, dict]]:
        """Événements en attente, du plus ancien au plus récent (FIFO)."""
        rows = self._conn.execute(
            "SELECT id, payload FROM outbox ORDER BY id ASC LIMIT ?", (limite,)
        ).fetchall()
        return [(int(i), json.loads(p)) for i, p in rows]

    def supprimer(self, id_: int) -> None:
        """Retire un événement acquitté."""
        self._conn.execute("DELETE FROM outbox WHERE id = ?", (id_,))
        self._conn.commit()

    def incrementer_essai(self, id_: int) -> None:
        self._conn.execute("UPDATE outbox SET essais = essais + 1 WHERE id = ?", (id_,))
        self._conn.commit()

    def taille(self) -> int:
        (n,) = self._conn.execute("SELECT COUNT(*) FROM outbox").fetchone()
        return int(n)

    def fermer(self) -> None:
        self._conn.close()
