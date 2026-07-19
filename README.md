# Wash Manager — Système de Monitoring IA pour Lavage Auto

Plateforme de supervision d'une station de lavage automobile basée sur la vision
par ordinateur. Le système compte les véhicules, lit les plaques (LPR), classe
automatiquement le forfait réellement effectué (Rapide / Premium / Complet),
suit la performance des employés, détecte les anomalies de facturation et génère
un rapport journalier.

> **État du dépôt : SQUELETTE / GROS PLAN.**
> Ce dépôt fournit l'architecture complète et tous les points d'entrée, mais
> **la finition et le raccordement du code réel restent à faire par le·la
> développeur·euse**. Chaque emplacement à compléter est balisé par un
> commentaire `TODO(dev):`. Cherchez-les avec :
> ```bash
> grep -rn "TODO(dev)" .
> ```

## Architecture (4 couches)

```
  ┌────────────┐   ┌───────────────┐   ┌──────────────┐   ┌─────────────────┐
  │ CAPTATION  │→ │  TRAITEMENT IA │→ │  STOCKAGE     │→ │  VISUALISATION  │
  │ Caméras IP │   │  Serveur edge  │   │  PostgreSQL   │   │  Dashboard web  │
  │ + LPR      │   │  (ai/)         │   │  (backend/)   │   │  + PWA mobile   │
  └────────────┘   └───────────────┘   └──────────────┘   └─────────────────┘
```

| Dossier      | Rôle                                                            |
|--------------|-----------------------------------------------------------------|
| `ai/`        | Pipeline edge : détection YOLO, tracking, LPR, zones, orchestrateur. Émet des **événements** vers le backend. |
| `backend/`   | API FastAPI : ingestion des événements, base de données, classification des forfaits, anomalies, rapports, auth. |
| `frontend/`  | Dashboard React + Tailwind (PWA) : temps réel, KPI, historique, config. |
| `docs/`      | Documentation d'architecture et cahier des charges.             |

## Flux de données (résumé)

1. `ai/` lit les flux caméra, détecte + suit chaque véhicule à travers les zones
   (Entrée → Lavage → Aspiration → Polish → Sortie) et lit la plaque à l'entrée.
2. À chaque franchissement de ligne / présence en zone, `ai/` envoie un
   **événement** à l'API backend (`POST /api/v1/events`).
3. Le backend construit la **transaction** du véhicule, la rapproche du ticket
   POS (forfait payé), **classe le forfait réellement effectué** et **détecte
   les anomalies**.
4. Le **dashboard** consomme l'API (REST + WebSocket) pour l'affichage temps réel,
   et un job planifié génère le **rapport journalier** (PDF + WhatsApp).

## Démarrage rapide (dev)

```bash
cp .env.example .env          # ajustez les variables
docker compose up -d          # postgres + backend + frontend
# Backend  : http://localhost:8000/docs  (OpenAPI)
# Frontend : http://localhost:5173
```

Voir `backend/README.md`, `ai/README.md`, `frontend/README.md` pour le détail de
chaque brique et la liste des `TODO(dev)`.

## Développer sans caméras (données de démo)

Tant que le matériel n'est pas installé, on peut faire vivre tout le système
sans une seule caméra :

```bash
# 1. Données de référence (forfaits + compte admin@wash.local / changeme)
python -m app.db.seed

# 2a. Jeu de démo direct (plusieurs jours d'historique pour dashboard/rapports)
python -m app.db.demo 7 25        # 7 jours × ~25 véhicules

# 2b. OU simulateur temps réel (émet des événements comme une vraie caméra,
#     teste toute la chaîne d'ingestion + rapprochement + anomalies)
cd ai && python simulator.py --count 30 --anomaly-rate 0.2
```

Le dashboard, les KPI, l'historique, les anomalies et le rapport PDF sont alors
pleinement fonctionnels.

## Feuille de route (phases)

Le système est conçu pour un déploiement **progressif** — chaque phase apporte de
la valeur sans attendre le système complet :

1. **Infrastructure** — caméras, réseau, serveur edge.
2. **Détection + comptage** — YOLO + tracking + zones.
3. **LPR** — lecture des plaques marocaines.
4. **Classification forfaits + anomalies** — cœur métier.
5. **Suivi employés** — badges NFC + métriques.
6. **Dashboard + rapports** — interface web, PDF, alertes WhatsApp.
7. **Tests terrain + calibration**.
8. **Mise en production**.
