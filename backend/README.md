# Backend — API FastAPI

API REST + WebSocket qui reçoit les événements du pipeline IA, tient la base de
données, classe les forfaits, détecte les anomalies et génère les rapports.

## Structure

```
app/
├── main.py              # point d'entrée FastAPI, montage des routes
├── core/
│   ├── config.py        # settings (pydantic-settings)
│   ├── database.py      # engine + session SQLAlchemy
│   └── security.py      # JWT, hachage mot de passe, clé d'ingestion IA
├── models/              # tables SQLAlchemy (véhicules, employés, forfaits,
│                        #   transactions, anomalies, rapports, utilisateurs)
├── schemas/             # schémas Pydantic (I/O de l'API)
├── api/
│   ├── deps.py          # dépendances (auth, db session)
│   └── routes/          # un fichier par ressource
└── services/            # logique métier
    ├── classification.py  # ★ CŒUR : classification du forfait effectué
    ├── anomalie.py        # ★ règles de détection d'anomalies
    ├── ingestion.py       # transforme les événements IA en transactions
    ├── rapport.py         # rapport journalier (PDF)
    └── notification.py    # alertes WhatsApp
```

## Points à finir (`TODO(dev)`)

- Brancher Alembic pour les migrations (les modèles sont prêts).
- Implémenter le rapprochement POS ↔ véhicule (dépend de votre système de caisse).
- Générer le PDF réel (ReportLab) et envoyer via WhatsApp Business API.
- Durcir l'auth (rôles, rate-limiting) avant la production.

## Lancer en local (sans Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Seed des forfaits/données de démo :
python -m app.db.seed
```
