-- PostGIS Schema for Thai Electrical Distribution Network
-- GridTokenX Smart Meter Simulator
-- Requires: PostgreSQL 14+ with PostGIS 3.3+

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create schema for grid data
CREATE SCHEMA IF NOT EXISTS grid;

-- Set search path
SET search_path TO grid, public;

-- ============================================================================
-- TABLE: substations
-- High/Medium voltage substations (EGAT, MEA, PEA)
-- ============================================================================
CREATE TABLE grid.substations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    voltage_level_kv NUMERIC(6,1) NOT NULL, -- 500, 230, 115, 22
    operator VARCHAR(100), -- EGAT, MEA, PEA
    type VARCHAR(50), -- transmission, sub_transmission, distribution
    capacity_mva NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'in_service',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location::geometry)) STORED,
    longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location::geometry)) STORED,
    address TEXT,
    province VARCHAR(100),
    district VARCHAR(100),
    subdistrict VARCHAR(100),
    postal_code VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for substations
CREATE INDEX idx_substations_location ON grid.substations USING GIST (location);
CREATE INDEX idx_substations_province ON grid.substations(province);
CREATE INDEX idx_substations_voltage ON grid.substations(voltage_level_kv);

-- ============================================================================
-- TABLE: transformers
-- Distribution transformers (MV/LV)
-- ============================================================================
CREATE TABLE grid.transformers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    code VARCHAR(50) UNIQUE,
    substation_id INTEGER REFERENCES grid.substations(id),
    voltage_primary_kv NUMERIC(6,1) DEFAULT 22.0,
    voltage_secondary_kv NUMERIC(6,1) DEFAULT 0.4,
    capacity_kva NUMERIC(10,2),
    phase_count INTEGER DEFAULT 3,
    cooling_type VARCHAR(50), -- ONAN, ONAF, etc.
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    installation_date DATE,
    status VARCHAR(20) DEFAULT 'in_service',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location::geometry)) STORED,
    longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location::geometry)) STORED,
    pole_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for transformers
CREATE INDEX idx_transformers_location ON grid.transformers USING GIST (location);
CREATE INDEX idx_transformers_substation ON grid.transformers(substation_id);
CREATE INDEX idx_transformers_status ON grid.transformers(status);

-- ============================================================================
-- TABLE: power_lines
-- Transmission and distribution lines
-- ============================================================================
CREATE TABLE grid.power_lines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    code VARCHAR(50) UNIQUE,
    from_substation_id INTEGER REFERENCES grid.substations(id),
    to_substation_id INTEGER REFERENCES grid.substations(id),
    voltage_level_kv NUMERIC(6,1) NOT NULL,
    line_type VARCHAR(50), -- overhead, underground, submarine
    circuit_count INTEGER DEFAULT 1,
    conductor_type VARCHAR(100), -- e.g., NA2XS2Y 1x185 RM/25 12/20 kV
    conductor_material VARCHAR(50), -- AAC, AAAC, ACSR, Copper
    cross_section_mm2 NUMERIC(10,2),
    length_km NUMERIC(10,2) GENERATED ALWAYS AS (ST_Length(geom::geography) / 1000) STORED,
    resistance_ohm_km NUMERIC(10,6),
    reactance_ohm_km NUMERIC(10,6),
    capacitance_nf_km NUMERIC(10,2),
    ampacity_a NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'in_service',
    construction_date DATE,
    geom GEOGRAPHY(LINESTRING, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for power lines
CREATE INDEX idx_power_lines_geom ON grid.power_lines USING GIST (geom);
CREATE INDEX idx_power_lines_voltage ON grid.power_lines(voltage_level_kv);
CREATE INDEX idx_power_lines_status ON grid.power_lines(status);

-- ============================================================================
-- TABLE: meters
-- Smart meters (AMI) connected to the grid
-- ============================================================================
CREATE TABLE grid.meters (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(100) UNIQUE NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    meter_type VARCHAR(50), -- solar_prosumer, grid_consumer, hybrid, battery, ev_charger
    accuracy_class VARCHAR(20), -- CLASS_0_2, CLASS_0_5, CLASS_1_0, CLASS_2_0
    transformer_id INTEGER REFERENCES grid.transformers(id),
    phase_count INTEGER DEFAULT 1,
    rated_current_a NUMERIC(10,2),
    rated_voltage_v NUMERIC(10,2) DEFAULT 230,
    communication_type VARCHAR(50), -- WiFi, LoRaWAN, NB-IoT, PLC
    public_key TEXT, -- Ed25519 public key for signing
    status VARCHAR(20) DEFAULT 'active',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_Y(location::geometry)) STORED,
    longitude DOUBLE PRECISION GENERATED ALWAYS AS (ST_X(location::geometry)) STORED,
    address TEXT,
    province VARCHAR(100),
    district VARCHAR(100),
    customer_id VARCHAR(100),
    customer_name VARCHAR(255),
    installation_date DATE,
    last_reading_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for meters
CREATE INDEX idx_meters_location ON grid.meters USING GIST (location);
CREATE INDEX idx_meters_transformer ON grid.meters(transformer_id);
CREATE INDEX idx_meters_type ON grid.meters(meter_type);
CREATE INDEX idx_meters_status ON grid.meters(status);
CREATE INDEX idx_meters_province ON grid.meters(province);

-- ============================================================================
-- TABLE: meter_readings
-- Time-series meter readings (partitioned by date)
-- ============================================================================
CREATE TABLE grid.meter_readings (
    id BIGSERIAL,
    meter_id VARCHAR(100) NOT NULL REFERENCES grid.meters(meter_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    energy_generated_kwh NUMERIC(12,6) DEFAULT 0,
    energy_consumed_kwh NUMERIC(12,6) DEFAULT 0,
    battery_level_kwh NUMERIC(12,6),
    voltage_v NUMERIC(10,2),
    current_a NUMERIC(10,2),
    frequency_hz NUMERIC(10,4),
    power_factor NUMERIC(5,4),
    active_power_kw NUMERIC(12,6),
    reactive_power_kvar NUMERIC(12,6),
    signature TEXT, -- Ed25519 signature
    quality_flag VARCHAR(20), -- valid, estimated, invalid
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- Indexes for meter_readings
CREATE INDEX idx_meter_readings_meter_ts ON grid.meter_readings (meter_id, timestamp DESC);
CREATE INDEX idx_meter_readings_timestamp ON grid.meter_readings (timestamp DESC);

-- ============================================================================
-- TABLE: zones
-- Geographic zones (MEA/PEA service areas)
-- ============================================================================
CREATE TABLE grid.zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    zone_type VARCHAR(50), -- mea_area, pea_area, province, district
    operator VARCHAR(100), -- MEA, PEA
    area_km2 NUMERIC(10,2) GENERATED ALWAYS AS (ST_Area(geom::geography) / 1000000) STORED,
    geom GEOGRAPHY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for zones
CREATE INDEX idx_zones_geom ON grid.zones USING GIST (geom);
CREATE INDEX idx_zones_type ON grid.zones(zone_type);

-- ============================================================================
-- TABLE: network_topology
-- Graph representation for power flow analysis
-- ============================================================================
CREATE TABLE grid.network_topology (
    id SERIAL PRIMARY KEY,
    from_node_id INTEGER NOT NULL, -- bus/substation ID
    to_node_id INTEGER NOT NULL, -- bus/substation ID
    line_id INTEGER REFERENCES grid.power_lines(id),
    transformer_id INTEGER REFERENCES grid.transformers(id),
    impedance_r NUMERIC(10,6), -- Resistance (ohm)
    impedance_x NUMERIC(10,6), -- Reactance (ohm)
    impedance_z NUMERIC(10,6) GENERATED ALWAYS AS (SQRT(impedance_r^2 + impedance_x^2)) STORED,
    status VARCHAR(20) DEFAULT 'closed', -- closed, open, fault
    switch_type VARCHAR(50), -- circuit_breaker, disconnect_switch, auto_transfer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topology_from ON grid.network_topology(from_node_id);
CREATE INDEX idx_topology_to ON grid.network_topology(to_node_id);
CREATE INDEX idx_topology_status ON grid.network_topology(status);

-- ============================================================================
-- VIEWS: Common queries
-- ============================================================================

-- View: All grid assets by province
CREATE VIEW grid.vw_assets_by_province AS
SELECT 
    province,
    COUNT(DISTINCT s.id) as substations,
    COUNT(DISTINCT t.id) as transformers,
    COUNT(DISTINCT m.id) as meters,
    SUM(COALESCE(s.capacity_mva, 0)) as total_substation_capacity_mva,
    SUM(COALESCE(t.capacity_kva, 0)) as total_transformer_capacity_kva
FROM grid.substations s
FULL OUTER JOIN grid.transformers t ON s.province = t.location
FULL OUTER JOIN grid.meters m ON s.province = m.province
GROUP BY province;

-- View: Network statistics
CREATE VIEW grid.vw_network_stats AS
SELECT 
    voltage_level_kv,
    COUNT(DISTINCT sl.id) as line_count,
    SUM(ST_Length(sl.geom::geography) / 1000) as total_length_km,
    COUNT(DISTINCT sf.id) as from_substations,
    COUNT(DISTINCT st.id) as to_substations
FROM grid.power_lines sl
LEFT JOIN grid.substations sf ON sl.from_substation_id = sf.id
LEFT JOIN grid.substations st ON sl.to_substation_id = st.id
GROUP BY voltage_level_kv;

-- View: Active meters by transformer
CREATE VIEW grid.vw_meter_summary AS
SELECT 
    t.id as transformer_id,
    t.code as transformer_code,
    t.location as transformer_location,
    COUNT(m.id) as meter_count,
    SUM(CASE WHEN m.meter_type = 'solar_prosumer' THEN 1 ELSE 0 END) as solar_prosumers,
    SUM(CASE WHEN m.meter_type = 'grid_consumer' THEN 1 ELSE 0 END) as consumers,
    SUM(CASE WHEN m.meter_type = 'battery' THEN 1 ELSE 0 END) as battery_systems,
    SUM(CASE WHEN m.meter_type = 'ev_charger' THEN 1 ELSE 0 END) as ev_chargers
FROM grid.transformers t
LEFT JOIN grid.meters m ON t.id = m.transformer_id
GROUP BY t.id, t.code, t.location;

-- ============================================================================
-- FUNCTIONS: Utility functions
-- ============================================================================

-- Function: Find nearest transformer to a point
CREATE OR REPLACE FUNCTION grid.find_nearest_transformer(
    p_longitude DOUBLE PRECISION,
    p_latitude DOUBLE PRECISION,
    max_distance_m DOUBLE PRECISION DEFAULT 500
)
RETURNS TABLE (
    transformer_id INTEGER,
    code VARCHAR,
    distance_m DOUBLE PRECISION,
    capacity_kva NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.code,
        ST_Distance(
            t.location::geography,
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography
        ) as distance_m,
        t.capacity_kva
    FROM grid.transformers t
    WHERE ST_DWithin(
        t.location::geography,
        ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography,
        max_distance_m
    )
    ORDER BY distance_m
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Get meters in a radius
CREATE OR REPLACE FUNCTION grid.get_meters_in_radius(
    p_longitude DOUBLE PRECISION,
    p_latitude DOUBLE PRECISION,
    radius_m DOUBLE PRECISION DEFAULT 1000,
    p_meter_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    meter_id VARCHAR,
    meter_type VARCHAR,
    distance_m DOUBLE PRECISION,
    location GEOGRAPHY
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.meter_id,
        m.meter_type,
        ST_Distance(
            m.location::geography,
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography
        ) as distance_m,
        m.location
    FROM grid.meters m
    WHERE ST_DWithin(
        m.location::geography,
        ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography,
        radius_m
    )
    AND (p_meter_type IS NULL OR m.meter_type = p_meter_type)
    ORDER BY distance_m;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Export network as GeoJSON
CREATE OR REPLACE FUNCTION grid.export_network_geojson(
    p_voltage_min NUMERIC DEFAULT 0,
    p_voltage_max NUMERIC DEFAULT 500
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'type', 'FeatureCollection',
        'features', jsonb_agg(features.feature)
    ) INTO result
    FROM (
        -- Substations
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(location)::jsonb,
            'properties', jsonb_build_object(
                'type', 'substation',
                'name', name,
                'code', code,
                'voltage_level_kv', voltage_level_kv,
                'operator', operator,
                'capacity_mva', capacity_mva,
                'status', status
            )
        ) as feature
        FROM grid.substations
        WHERE voltage_level_kv BETWEEN p_voltage_min AND p_voltage_max
        
        UNION ALL
        
        -- Power Lines
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(geom)::jsonb,
            'properties', jsonb_build_object(
                'type', 'line',
                'name', name,
                'code', code,
                'voltage_level_kv', voltage_level_kv,
                'line_type', line_type,
                'length_km', length_km,
                'conductor_type', conductor_type,
                'status', status
            )
        ) as feature
        FROM grid.power_lines
        WHERE voltage_level_kv BETWEEN p_voltage_min AND p_voltage_max
        
        UNION ALL
        
        -- Transformers
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(location)::jsonb,
            'properties', jsonb_build_object(
                'type', 'transformer',
                'name', name,
                'code', code,
                'voltage_primary_kv', voltage_primary_kv,
                'voltage_secondary_kv', voltage_secondary_kv,
                'capacity_kva', capacity_kva,
                'status', status
            )
        ) as feature
        FROM grid.transformers
    ) as features;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- TRIGGERS: Auto-update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION grid.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_substations_updated_at BEFORE UPDATE ON grid.substations
    FOR EACH ROW EXECUTE FUNCTION grid.update_updated_at_column();

CREATE TRIGGER update_transformers_updated_at BEFORE UPDATE ON grid.transformers
    FOR EACH ROW EXECUTE FUNCTION grid.update_updated_at_column();

CREATE TRIGGER update_power_lines_updated_at BEFORE UPDATE ON grid.power_lines
    FOR EACH ROW EXECUTE FUNCTION grid.update_updated_at_column();

CREATE TRIGGER update_meters_updated_at BEFORE UPDATE ON grid.meters
    FOR EACH ROW EXECUTE FUNCTION grid.update_updated_at_column();

-- ============================================================================
-- COMMENTS: Documentation
-- ============================================================================

COMMENT ON SCHEMA grid IS 'Thai electrical distribution network data with PostGIS spatial support';
COMMENT ON TABLE grid.substations IS 'High and medium voltage substations (EGAT, MEA, PEA)';
COMMENT ON TABLE grid.transformers IS 'Distribution transformers (MV/LV)';
COMMENT ON TABLE grid.power_lines IS 'Transmission and distribution power lines';
COMMENT ON TABLE grid.meters IS 'Smart meters (AMI) for energy monitoring';
COMMENT ON TABLE grid.meter_readings IS 'Time-series meter readings (partitioned)';
COMMENT ON TABLE grid.zones IS 'Geographic service areas (MEA/PEA)';
COMMENT ON TABLE grid.network_topology IS 'Graph representation for power flow analysis';

-- Grant permissions (adjust as needed)
-- GRANT USAGE ON SCHEMA grid TO gridtokenx_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA grid TO gridtokenx_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA grid TO gridtokenx_user;
