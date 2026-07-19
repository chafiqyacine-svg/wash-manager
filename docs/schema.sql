-- Schéma de référence PostgreSQL (documentation).
-- La source de vérité reste les modèles SQLAlchemy (backend/app/models/).
-- TODO(dev): générer les vraies migrations avec Alembic ; ceci sert de repère.

CREATE TABLE vehicules (
    id              SERIAL PRIMARY KEY,
    plaque          VARCHAR(32) UNIQUE NOT NULL,
    premiere_visite TIMESTAMPTZ,
    derniere_visite TIMESTAMPTZ,
    nombre_visites  INTEGER DEFAULT 0,
    photo_reference VARCHAR(512),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE employes (
    id            SERIAL PRIMARY KEY,
    nom           VARCHAR(128) NOT NULL,
    badge_nfc_id  VARCHAR(64) UNIQUE,
    date_embauche DATE,
    site_id       INTEGER REFERENCES sites(id),  -- affectation (NULL = polyvalent)
    actif         BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_employes_site ON employes(site_id);

CREATE TABLE forfaits (
    id             SERIAL PRIMARY KEY,
    nom            VARCHAR(32) UNIQUE NOT NULL,   -- Rapide/Premium/Complet
    prix           NUMERIC(10,2) NOT NULL,
    zones_requises JSONB DEFAULT '[]',            -- ex: ["B","C","D"]
    temps_min      INTEGER NOT NULL,              -- minutes
    temps_max      INTEGER NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- Multi-emplacements : sites et leurs baies/stations.
CREATE TABLE sites (
    id         SERIAL PRIMARY KEY,
    nom        VARCHAR(128) NOT NULL,
    adresse    VARCHAR(255),
    actif      BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bays (
    id         SERIAL PRIMARY KEY,
    site_id    INTEGER NOT NULL REFERENCES sites(id),
    numero     INTEGER NOT NULL,
    statut     VARCHAR(20) DEFAULT 'operationnelle',  -- operationnelle | hors_service
    staff      INTEGER DEFAULT 0,
    actif      BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_bays_site ON bays(site_id);

CREATE TABLE transactions (
    id              SERIAL PRIMARY KEY,
    vehicule_id     INTEGER REFERENCES vehicules(id),
    employe_id      INTEGER REFERENCES employes(id),
    forfait_id      INTEGER REFERENCES forfaits(id),
    bay_id          INTEGER REFERENCES bays(id),
    track_id        VARCHAR(64),
    heure_entree    TIMESTAMPTZ,
    heure_sortie    TIMESTAMPTZ,
    duree_totale    INTEGER,                      -- secondes
    zone_b_debut    TIMESTAMPTZ, zone_b_fin TIMESTAMPTZ, zone_b_duree INTEGER,
    zone_c_debut    TIMESTAMPTZ, zone_c_fin TIMESTAMPTZ, zone_c_duree INTEGER,
    zone_d_debut    TIMESTAMPTZ, zone_d_fin TIMESTAMPTZ, zone_d_duree INTEGER,
    forfait_detecte VARCHAR(32),
    conforme        BOOLEAN,
    photo_entree    VARCHAR(512),
    photo_sortie    VARCHAR(512),
    statut          VARCHAR(16) DEFAULT 'en_cours',
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_transactions_track ON transactions(track_id);
CREATE INDEX idx_transactions_statut ON transactions(statut);

-- Caisse intégrée (remplace un POS externe tant qu'il n'y en a pas).
CREATE TABLE tickets (
    id             SERIAL PRIMARY KEY,
    forfait_id     INTEGER NOT NULL REFERENCES forfaits(id),
    prix           NUMERIC(10,2) NOT NULL,
    plaque         VARCHAR(32),                   -- facultatif (meilleur rapprochement)
    employe_id     INTEGER REFERENCES employes(id),
    reference      VARCHAR(64),
    heure          TIMESTAMPTZ DEFAULT now(),
    statut         VARCHAR(16) DEFAULT 'ouvert',  -- ouvert | rapproche | annule
    transaction_id INTEGER REFERENCES transactions(id),
    created_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_tickets_statut ON tickets(statut);
CREATE INDEX idx_tickets_plaque ON tickets(plaque);

CREATE TABLE anomalies (
    id             SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(id),
    type           VARCHAR(32) NOT NULL,
    severite       VARCHAR(16) NOT NULL,
    description    TEXT,
    heure          TIMESTAMPTZ DEFAULT now(),
    photo          VARCHAR(512),
    notifie        BOOLEAN DEFAULT FALSE,
    resolu         BOOLEAN DEFAULT FALSE
);

CREATE TABLE rapports_journaliers (
    id                   SERIAL PRIMARY KEY,
    date                 DATE UNIQUE NOT NULL,
    total_vehicules      INTEGER DEFAULT 0,
    total_ca             NUMERIC(12,2) DEFAULT 0,
    repartition_forfaits JSONB DEFAULT '{}',
    taux_conformite      NUMERIC(5,2) DEFAULT 0,
    nombre_anomalies     INTEGER DEFAULT 0,
    performance_employes JSONB DEFAULT '[]',
    fichier_pdf          VARCHAR(512),
    created_at           TIMESTAMPTZ DEFAULT now()
);

-- Paramètres configurables (clé-valeur) éditables depuis le dashboard.
CREATE TABLE parametres (
    cle         VARCHAR(64) PRIMARY KEY,
    valeur      TEXT NOT NULL,
    description TEXT,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE utilisateurs (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    nom             VARCHAR(128) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(32) DEFAULT 'manager',   -- admin | manager | caissier
    site_id         INTEGER REFERENCES sites(id),    -- NULL = tous les sites (admin)
    actif           BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);
