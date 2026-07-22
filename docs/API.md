# Référence API — Wash Manager

Base : `/api/v1`. Auth : **JWT** (`Authorization: Bearer …`) sauf endpoints edge
(protégés par la **clé d'ingestion** `X-AI-Key`). Rôles : `admin`, `manager`,
`caissier`. `resolve_site` force un manager/caissier sur *son* site.

Doc interactive complète : `GET /docs` (Swagger).

## Authentification
| Méthode | Chemin | Rôle | Description |
|---|---|---|---|
| POST | `/auth/login` | public | Connexion (form OAuth2) → JWT |
| GET | `/auth/me` | connecté | Profil (rôle + site) |

## Tableau de bord & exploitation
| Méthode | Chemin | Description |
|---|---|---|
| GET | `/dashboard/kpi` `/dashboard/en-cours` `/dashboard/apercu` `/dashboard/wash-details` `/dashboard/graphiques` | KPI, lavages en cours, baies, graphiques |
| GET/POST | `/queue` `/queue/demarrer` `/queue/terminer` | File d'attente (mode manuel) |
| GET/POST/PATCH | `/bays` … | Baies de lavage |
| GET | `/payments` | Vue financière (payé/en attente) |
| GET/GET | `/transactions` `/transactions/{id}` | Transactions |
| GET/POST | `/rapports` `/rapports/generer` | Rapport journalier (PDF) |

## Caisse & clôture
| Méthode | Chemin | Rôle | Description |
|---|---|---|---|
| GET/POST | `/tickets` | connecté | Consulter / encaisser (mode + site) |
| POST | `/tickets/{id}/annuler` | connecté | Annuler *(audité)* |
| POST | `/tickets/{id}/rapprocher` | connecté | Rapprochement manuel *(audité)* |
| GET | `/cloture/apercu` | connecté | Aperçu du jour par mode |
| POST | `/cloture` | admin/manager | Clôturer (1/jour/site) *(audité, alerte si écart)* |
| GET | `/cloture` | connecté | Historique |
| GET | `/cloture/{id}/pdf` | connecté | PDF (rapport Z) |

## Marges, inventaire, forfaits
| Méthode | Chemin | Description |
|---|---|---|
| GET | `/marges` `/marges/{forfait_id}` | Coût produits, marge, taux (par site) |
| GET/POST/PATCH/DELETE | `/produits` … | Inventaire (prix unitaire) *(mouvement/suppression audités)* |
| POST | `/produits/{id}/mouvement?delta=` | Entrée/sortie de stock *(audité)* |
| GET/POST/PUT/DELETE | `/forfaits` … | Forfaits *(modif/suppression auditées)* |
| GET/PUT | `/forfaits/{id}/consommation` | Recette de consommation |

## Objectifs & contrôle
| Méthode | Chemin | Rôle | Description |
|---|---|---|---|
| GET | `/objectifs/metriques` | connecté | Métriques disponibles |
| GET/POST/DELETE | `/objectifs` | admin/manager (POST/DELETE) | Cibles (upsert par site+métrique) |
| GET | `/objectifs/evaluation?jour=` | connecté | Réel vs cible + écart |
| GET | `/audit?action=` | admin/manager | Journal d'audit (site-scopé) |
| GET | `/cameras` | connecté | Santé caméras (en ligne/hors ligne) |
| GET | `/notifications` `/notifications/canaux` | admin/manager | Alertes + canaux |
| POST | `/notifications/test` | admin/manager | Envoyer une alerte de test |
| GET | `/export/recettes.csv` `/export/clotures.csv` | admin/manager | Export CSV |

## RH
| Méthode | Chemin | Description |
|---|---|---|
| GET/POST/PATCH | `/employes` … | Employés (site, couleur de gilet) |
| GET | `/employes/performance` `/employes/presence` `/employes/{id}/metriques` | Productivité, présence |
| GET/POST | `/pointage` | Pointage selfie horodaté serveur |
| GET/PUT | `/sites/{id}/horaires` `/employes/{id}/horaires` | Horaires |

## Anomalies, clients, config, admin
| Méthode | Chemin | Rôle | Description |
|---|---|---|---|
| GET | `/anomalies` | connecté | Liste (avec emplacement) |
| POST | `/anomalies/{id}/resoudre` | connecté | Résoudre *(audité)* |
| GET | `/vehicules` | connecté | Clients (par plaque) |
| GET/PUT | `/parametres` `/parametres/{cle}` | connecté | Paramètres configurables |
| GET/POST/PATCH | `/users` … | **admin** | Comptes & rôles |
| GET/POST | `/sites` | connecté | Sites (multi-emplacements) |

## Endpoints edge (clé d'ingestion `X-AI-Key`)
| Méthode | Chemin | Description |
|---|---|---|
| POST | `/events` | Ingestion d'un événement (entrée, zone, plaque, badge, sortie). `event_id` → idempotent |
| POST | `/events/heartbeat` | Signal de vie d'une caméra (supervision) |
| GET | `/events/palette-gilets` | Couleurs de gilet enregistrées (pour le matching edge) |
