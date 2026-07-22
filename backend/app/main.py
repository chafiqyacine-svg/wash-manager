"""Point d'entrée de l'API FastAPI — monte les routes et le scheduler."""
from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    anomalies,
    audit,
    auth,
    bays,
    cameras,
    cloture,
    dashboard,
    employes,
    events,
    forfaits,
    horaires,
    live,
    marges,
    parametres,
    payments,
    pointage,
    produits,
    queue,
    rapports,
    sites,
    tickets,
    transactions,
    users,
    vehicules,
)
from app.core.config import settings
from app.scheduler import demarrer_scheduler

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # Mémorise la boucle pour la diffusion WebSocket depuis les routes sync.
    live.manager.set_loop(asyncio.get_running_loop())
    # Démarrage : planifie le rapport journalier.
    scheduler = demarrer_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Wash Manager API", version="0.1.0", lifespan=lifespan)

# CORS — TODO(dev): restreindre aux origines du dashboard en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes protégées / publiques
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(events.router, prefix=API_PREFIX)
app.include_router(tickets.router, prefix=API_PREFIX)
app.include_router(sites.router, prefix=API_PREFIX)
app.include_router(bays.router, prefix=API_PREFIX)
app.include_router(cameras.router, prefix=API_PREFIX)
app.include_router(horaires.router, prefix=API_PREFIX)
app.include_router(queue.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(cloture.router, prefix=API_PREFIX)
app.include_router(pointage.router, prefix=API_PREFIX)
app.include_router(produits.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(vehicules.router, prefix=API_PREFIX)
app.include_router(employes.router, prefix=API_PREFIX)
app.include_router(forfaits.router, prefix=API_PREFIX)
app.include_router(marges.router, prefix=API_PREFIX)
app.include_router(parametres.router, prefix=API_PREFIX)
app.include_router(anomalies.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(rapports.router, prefix=API_PREFIX)
app.include_router(live.router, prefix=API_PREFIX)

# Stockage médias servi en statique (selfies de pointage, captures…).
os.makedirs(settings.media_root, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_root), name="media")


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "env": settings.api_env}
