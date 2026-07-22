# Modèle de données — Wash Manager

Tables principales (SQLAlchemy `app/models/`). Le schéma est géré par **Alembic**
(`alembic upgrade head`). Les tables marquées 🆕 ont été ajoutées après la v1.

## Cœur métier

**`sites`** — emplacements (multi-station).
**`bays`** — baies de lavage (rattachées à un site).
**`forfaits`** — services : `nom`, `prix`, `zones_requises` (JSON), `temps_min/max`.
**`vehicules`** — clients par plaque : `premiere/derniere_visite`, `nombre_visites`.
**`utilisateurs`** — comptes : `email`, `role` (admin/manager/caissier), `site_id`.
**`employes`** — laveurs : `badge_nfc_id`, **`couleur_gilet`** (identif. vision), `site_id`.

**`transactions`** — un passage véhicule (entité centrale) :
- suivi : `track_id`, `bay_id`, `heure_entree/sortie`, `duree_totale` ;
- zones : `zone_b/c/d_debut/fin/duree` ;
- résultat : `forfait_detecte`, `forfait_id` (payé), `conforme`, `statut`
  (en_cours/cloturee/abandonnee) ;
- **`inventaire_consomme`** (garde d'idempotence de la consommation stock).

**`tickets`** — caisse intégrée (source du « forfait payé ») :
- `forfait_id`, `prix`, `plaque`, `employe_id`, `statut` (ouvert/rapproche/annule) ;
- **`mode_paiement`** (espèce/carte/autre), **`site_id`** 🆕 (pour la clôture).

**`anomalies`** — écarts détectés : `type`, `severite`, `description`,
`transaction_id`/`employe_id`, `resolu`, `notifie`.

## Inventaire & recettes

**`produits`** — consommables par site : `nom`, `unite`, `quantite`,
`seuil_alerte`, **`prix_unitaire`** 🆕 (coût d'achat → marges).
**`forfait_produits`** — recette : `forfait_id`, `produit_id`, `lavages_par_unite`
(1 unité consommée tous les N lavages).

## Contrôle & pilotage 🆕

**`cloture_caisse`** — rapport Z : `jour`, `site_id`, `nb_tickets`,
`total_theorique`, `detail_modes` (JSON), `fond_caisse`, `montant_compte`,
`ecart`, `cloture_par_id`, `fichier_pdf`.

**`objectifs`** — cibles : `site_id` (NULL=global), `metrique`, `cible`, `sens`
(min/max), `actif`.

**`notifications`** — alertes : `canal` (whatsapp/email/log), `destinataire`,
`sujet`, `message`, `severite`, `statut` (en_attente/envoye/echec/simule),
`site_id`, `ref_type`/`ref_id`.

**`journal_audit`** — traçabilité : `utilisateur_id` + `utilisateur_email`/`role`
(snapshot), `action` (ex. `ticket.annuler`), `cible`/`cible_id`, `details` (JSON),
`site_id`, `created_at`.

**`cameras`** — supervision : `camera_id` (unique), `site_id`, `role`,
`derniere_vue`, `frames_traitees`, `events_envoyes`, `outbox_en_attente`.

## Fiabilité edge 🆕

**`evenements_traites`** — idempotence : `event_id` (unique) des événements déjà
appliqués (ignore les re-livraisons de la file locale de l'edge).

## Config & planification

**`parametres`** — clés/valeurs configurables (ex. fenêtre de rapprochement).
**`horaires_site`**, **`horaires_employe`** — plages d'ouverture / de travail.
**`pointages`** — pointages selfie horodatés serveur.
**`rapports_journaliers`** — agrégats du jour + PDF.

## Relations clés

```
site 1─* bay 1─* transaction *─1 forfait
site 1─* employe                transaction 1─* anomalie
site 1─* produit *─* forfait (via forfait_produits)
transaction 0/1─1 ticket (rapprochement)
site 1─* cloture_caisse / objectif / notification / camera / journal_audit
```

## Migrations (ordre)

`7a6b54f8d20b` (initial) → `4790a5b7512a` (inventaire_consomme) →
`b1c2d3e4f5a6` (prix_unitaire) → `c2d3e4f5a6b7` (clôture + ticket mode/site) →
`d3e4f5a6b7c8` (evenements_traites) → `e4f5a6b7c8d9` (cameras) →
`f5a6b7c8d9e0` (journal_audit) → `a6b7c8d9e0f1` (objectifs) →
`b7c8d9e0f1a2` (notifications).
