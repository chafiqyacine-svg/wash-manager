"""Fixtures de test : base SQLite jetable, données de référence, client API.

Le schéma est (re)créé à neuf pour chaque test → isolation totale.
"""
import os
import tempfile

# Doit être défini AVANT l'import de l'application (settings lit l'environnement).
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/wm_test.db")
os.environ.setdefault("MEDIA_ROOT", tempfile.mkdtemp())
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("AI_INGEST_API_KEY", "test-key")

import pytest  # noqa: E402

from app.core.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Bay, Forfait, Site, Utilisateur  # noqa: E402


@pytest.fixture
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def ref(db):
    """Données de référence : 3 forfaits, 2 sites, 1 baie sur le site 1."""
    rapide = Forfait(nom="Rapide", prix=30, zones_requises=["B"], temps_min=10, temps_max=20)
    premium = Forfait(nom="Premium", prix=60, zones_requises=["B", "C"], temps_min=20, temps_max=40)
    complet = Forfait(nom="Complet", prix=100, zones_requises=["B", "C", "D"], temps_min=35, temps_max=55)
    site1 = Site(nom="Site 1")
    site2 = Site(nom="Site 2")
    db.add_all([rapide, premium, complet, site1, site2])
    db.flush()
    bay = Bay(site_id=site1.id, numero=1, staff=2)
    db.add(bay)
    db.commit()
    return {"rapide": rapide, "premium": premium, "complet": complet,
            "site1": site1, "site2": site2, "bay": bay}


@pytest.fixture
def client(db, ref):
    """Client API authentifié en admin (dépendance get_db surchargée)."""
    from fastapi.testclient import TestClient

    from app.main import app

    db.add(Utilisateur(email="admin@test", nom="Admin",
                       hashed_password=hash_password("pw"), role="admin"))
    db.commit()

    def override_get_db():
        yield db  # session gérée par la fixture `db` (pas de close ici)

    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app)
    r = c.post("/api/v1/auth/login", data={"username": "admin@test", "password": "pw"})
    c.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    yield c
    app.dependency_overrides.clear()
