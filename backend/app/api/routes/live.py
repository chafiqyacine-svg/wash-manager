"""WebSocket temps réel : pousse les mises à jour aux dashboards connectés.

Principe simple et robuste : le serveur ne pousse pas l'état complet mais un
signal « quelque chose a changé » (`{"type": "update"}`). Le frontend re-fetche
alors les données concernées. Cela découple le backend de la forme exacte de l'UI.

Les points de mutation (ingestion d'événements IA, file d'attente, tickets)
appellent `manager.notifier(...)`, thread-safe, pour diffuser à tous les clients.
"""
import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token

router = APIRouter(tags=["live"])


class GestionnaireConnexions:
    """Registre des WebSockets dashboard + diffusion thread-safe."""

    def __init__(self) -> None:
        self.actifs: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Mémorise la boucle asyncio (appelé au démarrage de l'app)."""
        self._loop = loop

    async def connecter(self, ws: WebSocket) -> None:
        await ws.accept()
        self.actifs.append(ws)

    def deconnecter(self, ws: WebSocket) -> None:
        if ws in self.actifs:
            self.actifs.remove(ws)

    async def diffuser(self, message: dict) -> None:
        for ws in list(self.actifs):
            try:
                await ws.send_json(message)
            except Exception:
                self.deconnecter(ws)

    def notifier(self, message: dict | None = None) -> None:
        """Déclenche une diffusion. Sûr à appeler depuis du code SYNC ou ASYNC.

        Les routes sync de FastAPI tournent dans un threadpool ; on planifie donc
        la coroutine sur la boucle principale de façon thread-safe.
        """
        if self._loop is None:
            return
        payload = message or {"type": "update"}
        asyncio.run_coroutine_threadsafe(self.diffuser(payload), self._loop)


manager = GestionnaireConnexions()


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket, token: str | None = Query(default=None)) -> None:
    # Authentification via token en query param (?token=...).
    if not token or decode_access_token(token) is None:
        await ws.close(code=1008)  # policy violation
        return
    await manager.connecter(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive ; messages entrants ignorés
    except WebSocketDisconnect:
        manager.deconnecter(ws)
