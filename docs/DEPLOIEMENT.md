# Guide de déploiement — Wash Manager

Ce guide explique comment mettre le système en production sur un serveur/VPS.

## 1. Prérequis

- Un serveur Linux (VPS) — 2 vCPU / 4 Go RAM suffisent pour démarrer.
- **Docker** et **Docker Compose** installés, OU Python 3.12 + Node 20 + PostgreSQL 16.
- Un nom de domaine (recommandé) pour le HTTPS.

## 2. Récupérer le code et configurer

```bash
git clone <votre-dépôt> wash-manager && cd wash-manager
cp .env.example .env
```

Éditez `.env` — **les valeurs à changer impérativement** :

| Variable | Rôle |
|----------|------|
| `POSTGRES_PASSWORD` | mot de passe base de données |
| `DATABASE_URL` | doit correspondre au mot de passe ci-dessus |
| `SECRET_KEY` | clé JWT — générez avec `openssl rand -hex 32` |
| `AI_INGEST_API_KEY` | clé partagée avec le pipeline caméra (`ai/`) |
| `MEDIA_BASE_URL` | URL publique de vos médias (ex: `https://mondomaine/media`) |
| `WHATSAPP_*` | identifiants WhatsApp Business (alertes + rapport) |

## 3. Démarrage avec Docker (recommandé)

```bash
docker compose up -d --build
```

Le service backend applique **automatiquement les migrations** (`alembic upgrade head`)
au démarrage, puis lance l'API. Ensuite, initialisez les données de référence :

```bash
docker compose exec backend python -m app.db.seed
```

Cela crée : les forfaits, les 2 sites de démo + baies + horaires, un inventaire de
départ, et un **compte admin** `admin@wash.local` / `changeme`.
**Changez ce mot de passe immédiatement** (écran Utilisateurs).

- API : `http://IP:8000/docs`  · Frontend : `http://IP:5173`

> Données de démonstration (facultatif, pour tester) :
> `docker compose exec backend python -m app.db.demo 7 25`

## 4. Sans Docker (manuel)

```bash
# Base de données : créez une base PostgreSQL et renseignez DATABASE_URL.
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head            # crée le schéma
python -m app.db.seed           # données de référence
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Frontend (autre terminal)
cd frontend && npm install && npm run build   # génère dist/
# servez dist/ derrière un serveur web (nginx) ou `npm run preview`
```

## 5. HTTPS & reverse proxy

En production, placez un reverse proxy (nginx ou Caddy) devant :
- `/api` et `/media` → backend (port 8000), **WebSocket activé** pour `/api/v1/ws/live`.
- le reste → le frontend (dist statique).

Exemple Caddy (`Caddyfile`) :
```
mondomaine.ma {
    handle /api/* { reverse_proxy localhost:8000 }
    handle /media/* { reverse_proxy localhost:8000 }
    handle { root * /var/www/wash-manager/frontend/dist ; file_server ; try_files {path} /index.html }
}
```
Caddy gère le certificat HTTPS automatiquement. ⚠️ Le pointage (selfie) nécessite
HTTPS pour accéder à la caméra du navigateur.

## 6. Migrations (évolutions futures du schéma)

Quand les modèles changent, **ne jamais** recréer la base — générez une migration :

```bash
cd backend
alembic revision --autogenerate -m "description du changement"
# relire le fichier généré dans alembic/versions/ puis :
alembic upgrade head
```

`alembic downgrade -1` annule la dernière migration. `alembic history` liste tout.

## 7. Sauvegardes

Sauvegarde quotidienne de PostgreSQL (à mettre dans un cron) :
```bash
docker compose exec -T db pg_dump -U washmanager washmanager > backup_$(date +%F).sql
```
Sauvegardez aussi le dossier des médias (`/data/media` — selfies de pointage).

Restauration : `docker compose exec -T db psql -U washmanager washmanager < backup.sql`.

## 8. Pipeline caméra (`ai/`) — sur le serveur edge

Le pipeline IA tourne **au lavage**, pas sur le serveur applicatif (voir `ai/README.md`).
Il pointe vers `BACKEND_EVENTS_URL` et s'authentifie avec `AI_INGEST_API_KEY`.
Tant que les caméras ne sont pas installées, la station fonctionne en **mode manuel**
(caisse + file d'attente) ou en **mode test vidéo** (`ai/detect_video.py`).

## 9. Mise à jour de l'application

```bash
git pull
docker compose up -d --build      # applique aussi les migrations au démarrage
```

## 10. Checklist de mise en production

- [ ] `.env` : mots de passe, `SECRET_KEY`, `AI_INGEST_API_KEY` changés.
- [ ] `alembic upgrade head` exécuté (auto via Docker).
- [ ] Compte admin par défaut : mot de passe changé, comptes managers/caissiers créés.
- [ ] HTTPS actif (reverse proxy) — obligatoire pour la caméra de pointage.
- [ ] Sauvegarde PostgreSQL planifiée (cron).
- [ ] WhatsApp Business configuré (si alertes souhaitées).
