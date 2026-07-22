"""Tests d'API (FastAPI TestClient) : auth, endpoints, permissions, multi-site."""
from app.core.security import hash_password
from app.models import Utilisateur


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_auth_me(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_login_mauvais_mot_de_passe(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin@test", "password": "x"})
    assert r.status_code == 401


def test_forfaits_listes(client, ref):
    r = client.get("/api/v1/forfaits")
    assert r.status_code == 200
    assert {f["nom"] for f in r.json()} == {"Rapide", "Premium", "Complet"}


def test_token_invalide_refuse(client):
    r = client.get("/api/v1/forfaits", headers={"Authorization": "Bearer invalide"})
    assert r.status_code == 401


def test_creation_ticket(client, ref):
    r = client.post("/api/v1/tickets", json={"forfait_id": ref["rapide"].id, "plaque": "1-A-1"})
    assert r.status_code == 201
    assert r.json()["statut"] == "ouvert"


def test_palette_gilets_pour_edge(client, db, ref):
    """Le pipeline edge récupère les couleurs de gilet via la clé d'ingestion."""
    from app.models import Employe
    db.add_all([
        Employe(nom="A", site_id=ref["site1"].id, couleur_gilet="#E11D48"),
        Employe(nom="B", site_id=ref["site1"].id, couleur_gilet="#2563EB"),
        Employe(nom="C", site_id=ref["site1"].id, couleur_gilet=None),        # ignoré
        Employe(nom="D", site_id=ref["site1"].id, couleur_gilet="#059669", actif=False),  # ignoré
    ])
    db.commit()
    # Sans clé d'ingestion -> refusé.
    assert client.get("/api/v1/events/palette-gilets").status_code == 401
    # Avec la clé d'ingestion (edge).
    r = client.get("/api/v1/events/palette-gilets", headers={"X-AI-Key": "test-key"})
    assert r.status_code == 200
    assert sorted(r.json()["couleurs"]) == ["#2563EB", "#E11D48"]


def test_users_reserve_admin(client, db, ref):
    # crée un manager, se connecte en manager -> /users interdit (403)
    db.add(Utilisateur(email="mgr@test", nom="M", hashed_password=hash_password("pw"),
                       role="manager", site_id=ref["site1"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login", data={"username": "mgr@test", "password": "pw"}).json()["access_token"]
    r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_multisite_manager_voit_un_seul_site(client, db, ref):
    db.add(Utilisateur(email="mgr2@test", nom="M2", hashed_password=hash_password("pw"),
                       role="manager", site_id=ref["site2"].id))
    db.commit()
    tok = client.post("/api/v1/auth/login", data={"username": "mgr2@test", "password": "pw"}).json()["access_token"]
    r = client.get("/api/v1/sites", headers={"Authorization": f"Bearer {tok}"})
    noms = [s["nom"] for s in r.json()]
    assert noms == ["Site 2"]   # ne voit que son site
