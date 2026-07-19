"""WebSocket temps réel : pousse l'état du site aux dashboards connectés.

Le service d'ingestion (routes/events.py) publie les mises à jour ; ce module
les diffuse aux clients. SQUELETTE : gestion de connexions minimale, la
diffusion réelle est à brancher.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["live"])


class GestionnaireConnexions:
    """Registre simple des WebSockets dashboard connectés."""

    def __init__(self) -> None:
        self.actifs: list[WebSocket] = []

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


manager = GestionnaireConnexions()


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    # TODO(dev): authentifier la connexion WebSocket (token en query param).
    await manager.connecter(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive ; on ignore les messages entrants
    except WebSocketDisconnect:
        manager.deconnecter(ws)
