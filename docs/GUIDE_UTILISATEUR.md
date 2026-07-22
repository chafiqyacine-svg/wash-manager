# Guide utilisateur — Wash Manager

Mode d'emploi de la plateforme de gestion et de monitoring de stations de lavage.
Ce guide décrit **chaque écran** et **comment s'en servir au quotidien**.

## Sommaire
1. [Présentation](#1-présentation)
2. [Connexion et rôles](#2-connexion-et-rôles)
3. [Les deux modes de fonctionnement](#3-les-deux-modes-de-fonctionnement)
4. [Tableau de bord (Home)](#4-tableau-de-bord)
5. [Caisse (encaissement)](#5-caisse)
6. [Queue Management (file d'attente)](#6-queue-management)
7. [Bay Management (baies)](#7-bay-management)
8. [Employés](#8-employés)
9. [Pointage](#9-pointage)
10. [Présence & ponctualité](#10-présence--ponctualité)
11. [Payments (paiements)](#11-payments)
12. [Inventory (inventaire)](#12-inventory)
13. [Anomalies](#13-anomalies)
14. [Historique](#14-historique)
15. [Rapports](#15-rapports)
16. [Configuration (Settings)](#16-configuration)
17. [Utilisateurs](#17-utilisateurs)

---

## 1. Présentation

Wash Manager gère **plusieurs stations de lavage** depuis un seul système. Il suit
les véhicules, la caisse, la file d'attente, les employés (identification,
pointage, performance), l'inventaire, et détecte les anomalies. Il fonctionne
**avec ou sans caméras** (voir §3).

## 2. Connexion et rôles

Connectez-vous avec votre email et mot de passe. Trois rôles :

- **Admin** : accès total, gère les utilisateurs et tous les sites.
- **Manager** : gère **son site** uniquement (il ne voit que ses données).
- **Caissier** : caisse et file d'attente de son site.

> Sécurité multi-site : un manager/caissier rattaché à un site ne voit **que**
> son emplacement, partout dans l'application.

## 3. Les deux modes de fonctionnement

- **Mode manuel** (sans caméras) : l'opérateur encaisse en **Caisse**, puis gère
  les lavages en **Queue Management** (démarrer / terminer). Tout marche dès
  aujourd'hui, sans matériel.
- **Mode IA** (avec caméras) : le pipeline détecte les véhicules, lit les plaques,
  identifie l'employé (badge NFC ou couleur de gilet) et alimente le système
  automatiquement. Les deux modes coexistent.

## 4. Tableau de bord

Vue d'ensemble de la journée. En haut à droite, un **sélecteur de site**
(« Tous les sites » ou un site précis).

- **4 cartes KPI** : lavages en cours, en attente, terminés, chiffre d'affaires —
  avec l'évolution **vs la veille**.
- **Wash Details** : les lavages du jour (véhicule, catégorie, baie, statut
  Ontime/Delayed, montant).
- **Wash Bay Stations** : l'état de chaque baie (onglets Operational / Out of
  service / All) — lavage en cours, file, temps moyen, effectif.
- **Transactions** : derniers paiements (Paid / Pending).
- **Package Analytics** : graphiques (volume horaire, tendance 7 jours,
  répartition des forfaits, CA).
- **Recent Events** : dernières anomalies et alertes, avec leur emplacement.

Le tableau de bord se **rafraîchit en temps réel** (pas besoin de recharger).

## 5. Caisse

Pour **encaisser** un client : saisir la plaque (facultatif mais recommandé),
puis cliquer sur le forfait payé (Rapide / Premium / Complet…). Un **ticket** est
créé ; il sera rapproché automatiquement du véhicule détecté, ou utilisé pour
démarrer un lavage en file d'attente.

## 6. Queue Management

La **file d'attente** (mode manuel). Deux colonnes :
- **En attente** : les tickets payés non encore lavés. Choisissez une baie et
  cliquez **Démarrer**.
- **En cours** : les lavages en cours. Cliquez **Terminer** quand c'est fini.

C'est le cœur de l'exploitation **sans caméras**.

## 7. Bay Management

Gère les **baies** de chaque site :
- Basculer une baie **Opérationnelle / Hors service** (clic sur le badge).
- Ajuster l'**effectif** (staff) avec −/+.
- **Ajouter** une baie à un site.

## 8. Employés

- **Effectif** par site : chaque employé a un **badge NFC**, une **couleur de
  gilet** (pour l'identification par caméra), un **site d'affectation** et un
  statut actif.
- **Horaires** : bouton « Éditer » pour définir les créneaux de travail de la
  semaine.
- **Classement** : podium de performance (véhicules, temps moyen, conformité,
  revenus, score) sur 1 / 7 / 30 jours.

## 9. Pointage

**Pointage d'arrivée / départ par selfie.** L'employé se sélectionne, choisit
Arrivée ou Départ, puis **se prend en photo en direct** (caméra). Le système
**horodate la photo côté serveur** — impossible d'antidater avec une ancienne
image. Si l'arrivée dépasse la tolérance de retard, une **alerte** est levée.

> Nécessite un navigateur avec accès caméra (HTTPS en production).

## 10. Présence & ponctualité

Tableau du jour (par site) : pour chaque employé, **statut** (présent / absent /
non planifié), **retard**, heures d'**arrivée/départ**, **temps présent**, **temps
actif** (lavages), **temps mort** et **productivité**. Idéal pour le suivi RH et
la paie.

## 11. Payments

Vue financière : liste des transactions avec statut **Paid** (facturé) / **Pending**
(lavé sans ticket = recette en attente), et les **totaux** encaissé / en attente.
Bouton **Encaisser** pour ouvrir la caisse. Filtrable par site.

## 12. Inventory

**Stock des consommables** par site (shampoing, cire, etc.) :
- Ajuster le stock avec −/+/+10, **ajouter** ou retirer un produit.
- **Alerte de réapprovisionnement** quand un produit passe sous son seuil (ligne
  surlignée + bandeau).
- Le stock se **décrémente automatiquement** à chaque lavage, selon la recette du
  forfait (voir Configuration).

## 13. Anomalies

Liste des écarts détectés, chacun avec sa **sévérité**, son **emplacement (site)**
et le **véhicule** ou l'employé concerné :
- **Forfait non respecté** (payé plus que fait), **lavage non facturé**, **ticket
  fantôme**, **temps anormal**, **plaque non lue**, **lavage hors horaires**.
- Alertes RH : **retard**, **absence**.

Cliquez **Résoudre** une fois traitée. Les anomalies critiques/hautes remontent
aussi en temps réel dans Recent Events.

## 14. Historique

Recherche des transactions passées (véhicule, catégorie, durée, conformité,
statut). Sert à retrouver un lavage précis ou analyser les tendances.

## 15. Rapports

**Rapport journalier** automatique (chaque soir à l'heure configurée) : nombre de
véhicules, chiffre d'affaires, répartition des forfaits, taux de conformité,
performance des employés, anomalies. Généré en **PDF** et archivé ; on peut aussi
le régénérer à la demande.

## 16. Configuration

Réservé aux réglages :
- **Fenêtre de rapprochement** ticket ↔ véhicule (minutes).
- **Forfaits** : prix, zones requises, temps min/max ; **créer/supprimer** un
  service — et définir en même temps **les produits consommés** (« 1 unité tous
  les N lavages »).
- **Horaires d'ouverture** par site.
- **Consommation produits par forfait** (recette d'inventaire).

## 17. Utilisateurs

*(Admin uniquement.)* Créer des comptes, attribuer un **rôle** (admin / manager /
caissier) et un **site**, activer/désactiver. C'est ici qu'on cadre qui voit quoi.

---

### Cycle type d'une journée (mode manuel)
1. Le client paie → **Caisse** (ticket).
2. **Queue Management** → Démarrer sur une baie → Terminer.
3. Le **stock** baisse automatiquement ; l'**alerte réappro** se déclenche si bas.
4. Les employés **pointent** (arrivée/départ) ; retards/absences remontent en
   **Anomalies**.
5. Le soir, le **rapport journalier** est généré et envoyé.

## 18. Contrôle & pilotage (nouveautés)

- **Objectifs** : fixez des cibles (CA journalier, taux de conformité, lavages non
  facturés, véhicules). Le tableau du jour montre *cible vs réel* et signale en
  rouge les objectifs manqués.
- **Clôture de caisse** : en fin de journée, comptez les espèces ; le système
  affiche l'**écart** et archive un PDF (rapport Z). Une clôture par jour et par site.
- **Alertes** : les anomalies graves et les écarts de caisse déclenchent une
  notification (WhatsApp/email une fois les canaux configurés ; sinon « simulée »
  et visible ici). Bouton **Envoyer un test**.
- **Caméras** : état *en ligne / hors ligne* de chaque caméra. Une caméra muette
  (surveillance interrompue) apparaît en rouge.
- **Journal d'audit** : qui a annulé un ticket, changé un prix, résolu une anomalie,
  clôturé la caisse… avec date et utilisateur.
- **Export comptable** : téléchargez recettes et clôtures en **CSV** (Excel) sur une
  période, pour le comptable.
- **Marges** : coût des consommables et **marge** par forfait et par site.
- **Langue** : basculez **FR / ع** en haut de la barre latérale (l'arabe passe toute
  l'interface en droite-à-gauche).
