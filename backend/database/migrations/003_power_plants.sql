-- Migration: Add power_plants table to grid schema
-- Purpose: Store real-world power plant data from GeoJSON imports
-- Run: This migration should be applied after 001_postgis_grid_schema.sql

SET search_path TO grid, public;

-- ============================================================================
-- TABLE: power_plants
-- Real-world power plants (hydro, solar, wind, oil/gas, coal, biomass, etc.)
-- Source: EGAT, Department of Alternative Energy, IEA Thailand
-- ============================================================================
CREATE TABLE grid.power_plants (
    id SERIAL PRIMARY KEY,
    plant_id VARCHAR(100) UNIQUE NOT NULL, -- Unique identifier (e.g., "TH_HYDRO_0001")
    name VARCHAR(500) NOT NULL,
    name_th VARCHAR(500), -- Thai name if available
    plant_type VARCHAR(50) NOT NULL, -- hydropower, solar, wind, oil/gas, coal, bioenergy
    fuel_type VARCHAR(100), -- natural_gas, lignite, bituminous, etc.
    technology VARCHAR(100), -- combined_cycle, steam_turbine, PV, CFB, etc.
    
    -- Electrical specs
    capacity_mw NUMERIC(10,2) NOT NULL,
    units INTEGER DEFAULT 1, -- Number of generating units
    
    -- Operational status
    status VARCHAR(50) DEFAULT 'operating', -- operating, construction, planned, decommissioned
    start_year INTEGER, -- Commissioning year
    operator VARCHAR(255) DEFAULT 'EGAT', -- EGAT, GLOW, Gulf, RATCH, etc.
    
    -- Location
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location::geometry)) STORED,
    longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location::geometry)) STORED,
    province VARCHAR(100),
    region VARCHAR(50), -- bangkok, central, north, northeast, south, east
    location_accuracy VARCHAR(50) DEFAULT 'exact', -- exact, approximate, centroid
    
    -- Grid integration
    voltage_level_kv NUMERIC(6,1), -- Connection voltage (500, 230, 115, 22)
    grid_connection_type VARCHAR(50), -- transmission, distribution
    is_renewable BOOLEAN GENERATED ALWAYS AS (
        plant_type IN ('hydropower', 'solar', 'wind', 'bioenergy', 'geothermal')
    ) STORED,
    
    -- Environmental
    carbon_intensity_gco2_kwh NUMERIC(10,2), -- g CO2/kWh (null for renewables)
    
    -- Metadata
    source VARCHAR(255) DEFAULT 'OpenStreetMap/Global Power Plant Tracker',
    osm_id BIGINT, -- Original OSM ID if sourced from OSM
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index
CREATE INDEX idx_power_plants_location ON grid.power_plants USING GIST (location);

-- Functional indexes
CREATE INDEX idx_power_plants_type ON grid.power_plants(plant_type);
CREATE INDEX idx_power_plants_status ON grid.power_plants(status);
CREATE INDEX idx_power_plants_capacity ON grid.power_plants(capacity_mw);
CREATE INDEX idx_power_plants_renewable ON grid.power_plants(is_renewable);
CREATE INDEX idx_power_plants_region ON grid.power_plants(region);
CREATE INDEX idx_power_plants_operator ON grid.power_plants(operator);
CREATE INDEX idx_power_plants_start_year ON grid.power_plants(start_year);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: All operating plants by type
CREATE OR REPLACE VIEW grid.vw_plants_by_type AS
SELECT 
    plant_type,
    COUNT(*) as plant_count,
    SUM(capacity_mw) as total_capacity_mw,
    ROUND(AVG(capacity_mw), 2) as avg_capacity_mw,
    COUNT(*) FILTER (WHERE is_renewable = true) as renewable_count,
    SUM(capacity_mw) FILTER (WHERE is_renewable = true) as renewable_capacity_mw
FROM grid.power_plants
WHERE status = 'operating'
GROUP BY plant_type
ORDER BY total_capacity_mw DESC;

-- View: Plants by region
CREATE OR REPLACE VIEW grid.vw_plants_by_region AS
SELECT 
    region,
    COUNT(*) as plant_count,
    SUM(capacity_mw) as total_capacity_mw,
    COUNT(*) FILTER (WHERE is_renewable = true) as renewable_count,
    SUM(capacity_mw) FILTER (WHERE is_renewable = true) as renewable_capacity_mw,
    ROUND(SUM(capacity_mw) FILTER (WHERE is_renewable = true) / NULLIF(SUM(capacity_mw), 0) * 100, 2) as renewable_pct
FROM grid.power_plants
WHERE status = 'operating'
GROUP BY region
ORDER BY total_capacity_mw DESC;

-- View: Renewable energy summary
CREATE OR REPLACE VIEW grid.vw_renewable_summary AS
SELECT 
    COUNT(*) as total_plants,
    SUM(capacity_mw) as total_capacity_mw,
    plant_type,
    COUNT(*) as plant_count,
    SUM(capacity_mw) as capacity_mw,
    ROUND(SUM(capacity_mw) / (SELECT SUM(capacity_mw) FROM grid.power_plants WHERE status = 'operating') * 100, 2) as pct_of_total
FROM grid.power_plants
WHERE status = 'operating' AND is_renewable = true
GROUP BY plant_type
ORDER BY capacity_mw DESC;

-- View: Plants near substations (for grid integration)
CREATE OR REPLACE VIEW grid.vw_plants_near_substations AS
SELECT 
    pp.plant_id,
    pp.name,
    pp.plant_type,
    pp.capacity_mw,
    s.name as nearest_substation,
    s.voltage_level_kv as substation_voltage_kv,
    ROUND(ST_Distance(pp.location, s.location) / 1000, 2) as distance_km
FROM grid.power_plants pp
CROSS JOIN LATERAL (
    SELECT name, voltage_level_kv, location
    FROM grid.substations
    ORDER BY pp.location <-> location
    LIMIT 1
) s
WHERE pp.status = 'operating';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Find plants within radius
CREATE OR REPLACE FUNCTION grid.find_plants_in_radius(
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    radius_km DOUBLE PRECISION,
    plant_type_filter VARCHAR DEFAULT NULL,
    status_filter VARCHAR DEFAULT 'operating'
)
RETURNS TABLE (
    plant_id VARCHAR,
    name VARCHAR,
    plant_type VARCHAR,
    capacity_mw NUMERIC,
    distance_km DOUBLE PRECISION,
    is_renewable BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pp.plant_id,
        pp.name,
        pp.plant_type,
        pp.capacity_mw,
        ST_Distance(
            pp.location,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) / 1000 as distance_km,
        pp.is_renewable
    FROM grid.power_plants pp
    WHERE ST_DWithin(
        pp.location,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_km * 1000
    )
    AND (plant_type_filter IS NULL OR pp.plant_type = plant_type_filter)
    AND (status_filter IS NULL OR pp.status = status_filter)
    ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;

-- Function: Get capacity statistics
CREATE OR REPLACE FUNCTION grid.get_plant_capacity_stats()
RETURNS TABLE (
    total_capacity_mw NUMERIC,
    operating_capacity_mw NUMERIC,
    renewable_capacity_mw NUMERIC,
    renewable_pct NUMERIC,
    plant_count INTEGER,
    operating_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        SUM(capacity_mw) as total_capacity_mw,
        SUM(capacity_mw) FILTER (WHERE status = 'operating') as operating_capacity_mw,
        SUM(capacity_mw) FILTER (WHERE is_renewable = true AND status = 'operating') as renewable_capacity_mw,
        ROUND(
            SUM(capacity_mw) FILTER (WHERE is_renewable = true AND status = 'operating') / 
            NULLIF(SUM(capacity_mw) FILTER (WHERE status = 'operating'), 0) * 100, 
            2
        ) as renewable_pct,
        COUNT(*) as plant_count,
        COUNT(*) FILTER (WHERE status = 'operating') as operating_count
    FROM grid.power_plants;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update updated_at timestamp
CREATE OR REPLACE FUNCTION grid.update_power_plants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_power_plants_updated_at
    BEFORE UPDATE ON grid.power_plants
    FOR EACH ROW
    EXECUTE FUNCTION grid.update_power_plants_updated_at();

-- ============================================================================
-- GRANTS (adjust as needed for your setup)
-- ============================================================================
-- GRANT SELECT ON ALL TABLES IN SCHEMA grid TO gridtokenx_readonly;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA grid TO gridtokenx_app;

COMMENT ON TABLE grid.power_plants IS 'Real-world power plants in Thailand (hydro, solar, wind, oil/gas, coal, biomass)';
COMMENT ON COLUMN grid.power_plants.plant_id IS 'Unique plant identifier (e.g., TH_HYDRO_0001)';
COMMENT ON COLUMN grid.power_plants.is_renewable IS 'Auto-generated: true for hydro, solar, wind, bioenergy, geothermal';
