"""Tests de la supervision des caméras (heartbeat edge + statut en ligne)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Camera


def _cam(db, camera_id):
    return db.scalar(select(Camera).where(Camera.camera_id == camera_id))


def test_heartbeat_cree_puis_met_a_jour(client, db, ref):
    hb = {"camera_id": "cam_baie1", "site_id": ref["site1"].id, "role": "bay",
          "frames_traitees": 10, "events_envoyes": 3, "outbox_en_attente": 0}
    # Sans clé d'ingestion -> refusé.
    assert client.post("/api/v1/events/heartbeat", json=hb).status_code == 401
    r = client.post("/api/v1/events/heartbeat", json=hb, headers={"X-AI-Key": "test-key"})
    assert r.status_code == 200

    cam = _cam(db, "cam_baie1")
    assert cam.frames_traitees == 10 and cam.derniere_vue is not None

    # 2e heartbeat : upsert (pas de doublon), compteurs mis à jour.
    hb["frames_traitees"] = 25
    client.post("/api/v1/events/heartbeat", json=hb, headers={"X-AI-Key": "test-key"})
    assert db.query(Camera).filter(Camera.camera_id == "cam_baie1").count() == 1
    db.expire_all()
    assert _cam(db, "cam_baie1").frames_traitees == 25


def test_liste_cameras_statut_en_ligne(client, db, ref):
    now = datetime.now(timezone.utc)
    db.add_all([
        Camera(camera_id="recente", site_id=ref["site1"].id, role="bay",
               derniere_vue=now - timedelta(seconds=10)),      # en ligne
        Camera(camera_id="muette", site_id=ref["site1"].id, role="bay",
               derniere_vue=now - timedelta(minutes=10)),      # hors ligne
        Camera(camera_id="jamais_vue", site_id=ref["site1"].id, role="entree"),  # hors ligne
    ])
    db.commit()
    r = client.get("/api/v1/cameras")
    assert r.status_code == 200
    parlgn = {c["camera_id"]: c["en_ligne"] for c in r.json()}
    assert parlgn == {"recente": True, "muette": False, "jamais_vue": False}


def test_cameras_filtre_par_site(client, db, ref):
    db.add_all([
        Camera(camera_id="c1", site_id=ref["site1"].id),
        Camera(camera_id="c2", site_id=ref["site2"].id),
    ])
    db.commit()
    r = client.get(f"/api/v1/cameras?site_id={ref['site1'].id}")
    assert [c["camera_id"] for c in r.json()] == ["c1"]
