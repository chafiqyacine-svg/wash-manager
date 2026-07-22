# Documentation — Wash Manager

Système de monitoring IA + gestion de station de lavage auto (multi-sites, FR/AR,
utilisable sans caméra).

## Par où commencer

| Document | Pour qui | Contenu |
|---|---|---|
| **[FONCTIONNALITES.md](FONCTIONNALITES.md)** | tous | Catalogue de toutes les fonctionnalités, par thème |
| **[CHANGELOG.md](CHANGELOG.md)** | tous | Journal descriptif des évolutions (ce qui a été ajouté, pourquoi, comment) |
| **[GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)** | gérant / caissier | Comment utiliser chaque écran |
| **[GUIDE_DEVELOPPEUR.md](GUIDE_DEVELOPPEUR.md)** | développeur | Architecture du code, conventions, modules ajoutés |
| **[API.md](API.md)** | développeur / intégrateur | Référence des endpoints REST |
| **[MODELE_DONNEES.md](MODELE_DONNEES.md)** | développeur | Tables, colonnes, relations, migrations |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | technique | Vue d'ensemble des 4 couches |
| **[DEPLOIEMENT.md](DEPLOIEMENT.md)** | ops | Mise en production |
| **[HANDOFF_DEV.md](HANDOFF_DEV.md)** | développeur | Reste à faire (TODO dev) |
| **[../ai/README.md](../ai/README.md)** | technique | Pipeline IA, topologie caméras |
| **[schema.sql](schema.sql)** | référence | Schéma SQL |

## En une phrase

Le **pipeline IA** (edge) perçoit et émet des événements ; le **backend** décide
(classification, anomalies, consommation, alertes) ; le **frontend** affiche et
pilote. Chaque action à risque est tracée (audit), chaque objectif est suivi,
chaque encaissement est contrôlé (clôture) et exportable (CSV).
