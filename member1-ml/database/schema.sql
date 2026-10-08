-- ==============================================================================
-- VIT MAPATHON — Production Agricultural Monitoring Schema
-- PostGIS Spatial & Multi-Temporal Time-Series Schema
-- Target Area: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District
-- ==============================================================================

-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Base Agricultural Parcels (Cadastral Spatial Master Table)
CREATE TABLE IF NOT EXISTS agricultural_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    taluk VARCHAR(50) DEFAULT 'Ambasamudram',
    area_sq_km FLOAT NOT NULL,
    area_ha FLOAT NOT NULL,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parcels_geom 
    ON agricultural_parcels USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_parcels_id 
    ON agricultural_parcels (parcel_id);


-- 2. Multi-Temporal Parcel Observations (Time-Series Table)
-- Allows multiple satellite observations over years (2026, 2027, 2028...) to coexist
CREATE TABLE IF NOT EXISTS parcel_observations (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL REFERENCES agricultural_parcels(parcel_id) ON DELETE CASCADE,
    observation_date DATE NOT NULL,
    processing_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    crop VARCHAR(30) NOT NULL,
    crop_confidence FLOAT NOT NULL,
    prob_paddy FLOAT,
    prob_banana FLOAT,
    prob_other FLOAT,
    ndvi FLOAT,
    ndwi FLOAT,
    evi FLOAT,
    crop_health VARCHAR(30) DEFAULT 'Healthy',      -- 'Healthy', 'Moderate Stress', 'Severe Stress', 'Unknown'
    health_score FLOAT,                             -- Normalized agronomic vigor score (0.0 to 1.0)
    damage_percent FLOAT DEFAULT 0.0,              -- Calibrated damage percentage
    hazard VARCHAR(50) DEFAULT 'None',              -- 'None', 'Flood', 'Drought', 'Cyclone', 'Potential'
    severity VARCHAR(30) DEFAULT 'None',            -- 'None', 'Low', 'Moderate', 'High', 'Severe'
    hazard_evidence TEXT,                           -- Multi-temporal delta indicators justifying classification
    model_version VARCHAR(20) NOT NULL,             -- Active production model (e.g. 'v1.0')
    source_scene VARCHAR(120),                      -- Sentinel-2 product ID or tile reference
    area_ha FLOAT NOT NULL,
    area_sq_km FLOAT NOT NULL,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    CONSTRAINT uq_parcel_obs_date UNIQUE (parcel_id, observation_date)
);

-- Time-Series & Geospatial Indexes for High-Performance Queries
CREATE INDEX IF NOT EXISTS idx_obs_parcel_id 
    ON parcel_observations (parcel_id);

CREATE INDEX IF NOT EXISTS idx_obs_date 
    ON parcel_observations (observation_date DESC);

CREATE INDEX IF NOT EXISTS idx_obs_crop 
    ON parcel_observations (crop);

CREATE INDEX IF NOT EXISTS idx_obs_hazard 
    ON parcel_observations (hazard);

CREATE INDEX IF NOT EXISTS idx_obs_health 
    ON parcel_observations (crop_health);

CREATE INDEX IF NOT EXISTS idx_obs_model_ver 
    ON parcel_observations (model_version);

CREATE INDEX IF NOT EXISTS idx_obs_geom 
    ON parcel_observations USING GIST (geom);

-- Composite Index for Latest Observation Queries
CREATE INDEX IF NOT EXISTS idx_obs_parcel_date 
    ON parcel_observations (parcel_id, observation_date DESC);
