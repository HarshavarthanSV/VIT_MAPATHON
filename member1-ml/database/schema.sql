-- ==============================================================================
-- VIT MAPATHON — Member 1 (AI / ML & Backend Systems)
-- PostGIS Spatial Schema for Agricultural Land Parcels
-- Target Area: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District
-- ==============================================================================

-- Enable PostGIS spatial extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Agricultural Parcels Table
CREATE TABLE IF NOT EXISTS agricultural_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    predicted_crop VARCHAR(30) NOT NULL,
    confidence FLOAT NOT NULL,
    area_sq_km FLOAT NOT NULL,
    area_ha FLOAT NOT NULL,
    prob_paddy FLOAT,
    prob_banana FLOAT,
    prob_other FLOAT,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial GIST Index for high-performance spatial queries & bounding box lookups
CREATE INDEX IF NOT EXISTS idx_parcels_geom 
    ON agricultural_parcels USING GIST (geom);

-- B-Tree Index for crop category filtering (Paddy, Banana, Other)
CREATE INDEX IF NOT EXISTS idx_parcels_crop 
    ON agricultural_parcels (predicted_crop);

-- B-Tree Index for confidence filtering
CREATE INDEX IF NOT EXISTS idx_parcels_confidence 
    ON agricultural_parcels (confidence);
