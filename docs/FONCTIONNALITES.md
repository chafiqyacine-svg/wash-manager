# Wash Manager — Catalogue des fonctionnalités

Système de **monitoring IA + gestion** de station de lavage auto, multi-sites,
utilisable **sans caméra** (mode manuel + simulateur), en **français et arabe**.

Trois couches :

1. **`ai/`** (edge) — perçoit et émet des *événements* (n'a aucune logique métier) ;
2. **`backend/`** (FastAPI) — décide : classification, anomalies, consommation, alertes ;
3. **`frontend/`** (React) — affiche et pilote.

---

## 1. Exploitation quotidienne

| Fonction | Page | Description |
|----------|------|-------------|
| Tableau de bord | Accueil | KPI du jour, baies (Wash Bay Stations), graphiques (volume horaire, CA, forfaits), événements récents. Temps réel (WebSocket). |
| Caisse intégrée | Caisse | Encaissement (forfait + mode de paiement espèces/carte/autre + plaque) → rapproché automatiquement du véhicule détecté. |
| File d'attente | File d'attente | Mode manuel sans caméra : démarrer/terminer un lavage sur une baie. |
| Baies | Baies de lavage | Suivi et édition des postes de lavage par site. |
| Historique / Rapports | Historique, Rapports | Transactions passées ; rapport journalier PDF automatique. |

## 2. Clients & véhicules

- **Clients** : historique par plaque (nombre de visites, première/dernière visite).
- Reconnaissance de plaque (LPR) côté edge, rapprochement configurable (fenêtre en minutes).

## 3. Ressources humaines

| Fonction | Page | Description |
|----------|------|-------------|
| Employés | Employés | Fiches, rattachement à un site, **couleur de gilet** (identification par vision). |
| Pointage | Pointage | Pointage **selfie horodaté par le serveur** (anti-fraude). |
| Présence | Présence | Ponctualité, temps présent/actif/mort, productivité ; alertes retard/absence. |

## 4. Inventaire, coûts & rentabilité

- **Inventaire** : stock des consommables par site, seuil de réappro, **prix unitaire**.
- **Recette de consommation** : chaque forfait consomme 1 unité tous les *N* lavages.
- **Marges** (page *Marges*) : coût produits par lavage = Σ(prix unitaire ÷ lavages
  par unité) ; **marge** et **taux de marge** par forfait et par site.

## 5. Contrôle & pilotage *(cockpit du gérant)*

| Fonction | Page | Rôle | Description |
|----------|------|------|-------------|
| **Objectifs & écarts** | Objectifs | admin/manager | Cibles (CA journalier, taux de conformité, lavages non facturés, véhicules) comparées au réel du jour ; badge *Atteint/Manqué*. |
| **Clôture de caisse** | Clôture de caisse | tous | Rapport Z : encaissements par mode, comptage, **écart de caisse**, PDF, une par jour/site. |
| **Alertes** | Alertes | admin/manager | Notifications déclenchées (anomalie grave, écart de caisse) sur WhatsApp/email ; historique + statut. |
| **Anomalies** | Anomalies | tous | Lavage non facturé, forfait non respecté, ticket fantôme, temps anormal, hors horaires… avec emplacement. |
| **Journal d'audit** | Journal d'audit | admin/manager | Traçabilité : *qui* a annulé un ticket, changé un prix, résolu une anomalie, clôturé la caisse, ajusté le stock. |
| **Santé caméras** | Caméras | tous | État *en ligne / hors ligne* (heartbeat), frames/événements, file d'attente edge. |
| **Export comptable** | Export comptable | admin/manager | Recettes et clôtures en **CSV** (Excel FR) sur une période. |

## 6. Rôles & sécurité multi-site

- Rôles : **admin** (tout), **manager** (son site), **caissier** (encaissement).
- `resolve_site` force un manager/caissier sur *son* site sur chaque endpoint.
- Endpoints edge (événements, heartbeat, palette gilets) protégés par une **clé
  d'ingestion** distincte du JWT.

## 7. Multilingue FR / AR

- Bascule FR / ع dans la barre latérale, persistée.
- **RTL** complet en arabe (mise en page inversée).

## 8. Pipeline IA (edge)

- Détection + suivi (YOLO/ByteTrack), zones/lignes, LPR, **identification du
  laveur par gilet** (couleur → employé).
- **Topologie recommandée** : une caméra par baie (rôle `bay`) → `track_id` stable
  (préfixé par la caméra pour éviter les collisions).
- **Robustesse** : hystérésis des lignes + anti-rebond des zones (moins de faux
  positifs) ; **file locale durable** (aucun événement perdu en cas de coupure) ;
  **idempotence** (une re-livraison n'est pas appliquée deux fois) ; **heartbeat**
  de supervision ; palette de gilets chargée dynamiquement du backend.

## 9. Sans caméra (dev / démo)

- `python -m app.db.seed` puis `python -m app.db.demo 7 25` : données réalistes.
- `ai/simulator.py` : « fausse caméra » qui envoie des événements (dont anomalies
  et gilets) au backend.
- `ai/detect_video.py` : comptage fiable sur une vidéo filmée au téléphone.

---

Voir aussi : `ARCHITECTURE.md`, `GUIDE_UTILISATEUR.md`, `GUIDE_DEVELOPPEUR.md`,
`DEPLOIEMENT.md`, et `ai/README.md` (topologie caméras).
