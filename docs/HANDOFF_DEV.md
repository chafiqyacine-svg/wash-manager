# Passation développeur — points à finir (`TODO(dev)`)

Ce dépôt est un **squelette / gros plan**. L'architecture, les interfaces et la
logique métier déterministe (classification des forfaits, règles d'anomalies,
géométrie des zones) sont en place et **testées**. Restent à raccorder les
briques qui dépendent de l'environnement réel (modèles, caméras, caisse, UI).

> Lister tous les points : `grep -rn "TODO(dev)" .`

## Priorité 1 — chaîne de perception (`ai/`)
- [ ] Fournir les poids YOLO (`ai/models/`) : détecteur véhicules + détecteur plaques.
- [ ] `pipeline/detector.py` — brancher l'inférence ultralytics.
- [ ] `pipeline/tracker.py` — brancher ByteTrack/DeepSORT (track_id stable).
- [ ] `pipeline/camera.py` — ouverture/lecture RTSP + reconnexion.
- [ ] `pipeline/lpr.py` — OCR (EasyOCR/PaddleOCR) + affinage plaques marocaines.
- [ ] `run.py` — boucles de frames (un thread par caméra) + arrêt propre.
- [ ] `config.yaml` — **calibrer** lignes d'entrée/sortie et polygones de zones.
- [ ] `pipeline/events.py` — file de retry locale si le réseau tombe.

## Priorité 2 — logique serveur (`backend/`)
- [ ] `services/ingestion.py` — **rapprochement POS** (ticket ↔ véhicule) : c'est le
      point le plus dépendant de votre système de caisse. En déduire `forfait_paye`,
      `forfait_id`, `conforme`, puis **persister les anomalies** et déclencher les
      alertes.
- [ ] `services/ingestion.py` — résolution employé via badge NFC (`_on_badge`).
- [ ] `services/rapport.py` — requêtes d'agrégation + génération PDF (ReportLab).
- [ ] `services/notification.py` — appel réel WhatsApp Business API.
- [ ] `api/routes/live.py` — auth WebSocket + diffusion des mises à jour temps réel.
- [ ] Migrations **Alembic** (remplacer `create_all` de `db/seed.py`).
- [ ] Durcir l'auth (rôles, expiration, rate-limiting) avant production.
- [ ] Monter le stockage médias en statique (`app.mount("/media", ...)`).

## Priorité 3 — dashboard (`frontend/`)
- [ ] Câbler chaque page aux endpoints (URLs prêtes dans `src/api/client.js`).
- [ ] WebSocket temps réel dans `Dashboard`/`LiveView`.
- [ ] Flux vidéo (HLS/WebRTC) dans `LiveView`.
- [ ] Graphiques Recharts (volume horaire, répartition forfaits, perf employés).
- [ ] PWA : service worker + notifications push (manifest déjà présent).

## Déjà fait et testé ✅
- Modèle de données complet (SQLAlchemy + schéma SQL de référence).
- **Classification du forfait effectué** (zones + durée) — `services/classification.py`.
- **Règles de détection d'anomalies** (6 cas du cahier des charges) — `services/anomalie.py`.
- **Géométrie zones/lignes** (franchissement, point-dans-polygone) — `ai/pipeline/zones.py`.
- Contrat d'événements IA ↔ backend.
- Squelette d'API (auth JWT, events, dashboard, transactions, anomalies,
  employés, forfaits, rapports, WebSocket).
- Structure frontend (routing, auth, layout, pages).
- Tests unitaires : `pytest backend/tests` et `pytest ai/tests`.

## Ordre de mise en route conseillé (phases du cahier des charges)
1. Infra caméras/réseau/edge → 2. Détection+comptage → 3. LPR → 4. Classification
+ anomalies → 5. Suivi employés (NFC) → 6. Dashboard + rapports → 7. Tests terrain
→ 8. Production.
