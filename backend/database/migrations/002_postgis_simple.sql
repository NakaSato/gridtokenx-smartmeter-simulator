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
-- ============================================================================
CREATE TABLE grid.substations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    voltage_level_kv NUMERIC(6,1) NOT NULL,
    operator VARCHAR(100),
    type VARCHAR(50),
    capacity_mva NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'in_service',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    province VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_substations_location ON grid.substations USING GIST (location);
CREATE INDEX idx_substations_province ON grid.substations(province);

-- ============================================================================
-- TABLE: transformers
-- ============================================================================
CREATE TABLE grid.transformers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    code VARCHAR(50) UNIQUE,
    substation_id INTEGER REFERENCES grid.substations(id),
    voltage_primary_kv NUMERIC(6,1) DEFAULT 22.0,
    voltage_secondary_kv NUMERIC(6,1) DEFAULT 0.4,
    capacity_kva NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'in_service',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transformers_location ON grid.transformers USING GIST (location);
CREATE INDEX idx_transformers_substation ON grid.transformers(substation_id);

-- ============================================================================
-- TABLE: power_lines
-- ============================================================================
CREATE TABLE grid.power_lines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    code VARCHAR(50) UNIQUE,
    from_substation_id INTEGER REFERENCES grid.substations(id),
    to_substation_id INTEGER REFERENCES grid.substations(id),
    voltage_level_kv NUMERIC(6,1) NOT NULL,
    line_type VARCHAR(50),
    conductor_type VARCHAR(100),
    status VARCHAR(20) DEFAULT 'in_service',
    geom GEOGRAPHY(LINESTRING, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_power_lines_geom ON grid.power_lines USING GIST (geom);
CREATE INDEX idx_power_lines_voltage ON grid.power_lines(voltage_level_kv);

-- ============================================================================
-- TABLE: meters
-- ============================================================================
CREATE TABLE grid.meters (
    id SERIAL PRIMARY KEY,
    meter_id VARCHAR(100) UNIQUE NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    meter_type VARCHAR(50),
    transformer_id INTEGER REFERENCES grid.transformers(id),
    status VARCHAR(20) DEFAULT 'active',
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    province VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meters_location ON grid.meters USING GIST (location);
CREATE INDEX idx_meters_transformer ON grid.meters(transformer_id);
CREATE INDEX idx_meters_type ON grid.meters(meter_type);

-- ============================================================================
-- TABLE: meter_readings
-- ============================================================================
CREATE TABLE grid.meter_readings (
    id BIGSERIAL,
    meter_id VARCHAR(100) NOT NULL REFERENCES grid.meters(meter_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    energy_generated_kwh NUMERIC(12,6) DEFAULT 0,
    energy_consumed_kwh NUMERIC(12,6) DEFAULT 0,
    voltage_v NUMERIC(10,2),
    current_a NUMERIC(10,2),
    frequency_hz NUMERIC(10,4),
    signature TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meter_readings_meter_ts ON grid.meter_readings (meter_id, timestamp DESC);
CREATE INDEX idx_meter_readings_timestamp ON grid.meter_readings (timestamp DESC);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Find nearest transformer
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

-- Get meters in radius
CREATE OR REPLACE FUNCTION grid.get_meters_in_radius(
    p_longitude DOUBLE PRECISION,
    p_latitude DOUBLE PRECISION,
    radius_m DOUBLE PRECISION DEFAULT 1000,
    p_meter_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    meter_id VARCHAR,
    meter_type VARCHAR,
    distance_m DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.meter_id,
        m.meter_type,
        ST_Distance(
            m.location::geography,
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography
        ) as distance_m
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

-- Export network as GeoJSON
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
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(location)::jsonb,
            'properties', jsonb_build_object(
                'type', 'substation',
                'name', name,
                'code', code,
                'voltage_level_kv', voltage_level_kv,
                'operator', operator,
                'status', status
            )
        ) as feature
        FROM grid.substations
        WHERE voltage_level_kv BETWEEN p_voltage_min AND p_voltage_max
        
        UNION ALL
        
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(geom)::jsonb,
            'properties', jsonb_build_object(
                'type', 'line',
                'name', name,
                'code', code,
                'voltage_level_kv', voltage_level_kv,
                'line_type', line_type,
                'status', status
            )
        ) as feature
        FROM grid.power_lines
        WHERE voltage_level_kv BETWEEN p_voltage_min AND p_voltage_max
        
        UNION ALL
        
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

-- Get network statistics
CREATE OR REPLACE FUNCTION grid.get_network_stats()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'substations_by_voltage', (
            SELECT jsonb_object_agg(voltage_level_kv, count)
            FROM (
                SELECT voltage_level_kv, COUNT(*) as count
                FROM grid.substations
                GROUP BY voltage_level_kv
                ORDER BY voltage_level_kv DESC
            ) sub
        ),
        'lines_by_voltage_km', (
            SELECT jsonb_object_agg(voltage_level_kv, total_km)
            FROM (
                SELECT voltage_level_kv, 
                       SUM(ST_Length(geom::geography) / 1000) as total_km
                FROM grid.power_lines
                GROUP BY voltage_level_kv
                ORDER BY voltage_level_kv DESC
            ) sub
        ),
        'meters_by_type', (
            SELECT jsonb_object_agg(meter_type, count)
            FROM (
                SELECT meter_type, COUNT(*) as count
                FROM grid.meters
                GROUP BY meter_type
            ) sub
        ),
        'total_substations', (SELECT COUNT(*) FROM grid.substations),
        'total_lines_km', (SELECT SUM(ST_Length(geom::geography) / 1000) FROM grid.power_lines),
        'total_meters', (SELECT COUNT(*) FROM grid.meters)
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Comments
COMMENT ON SCHEMA grid IS 'Thai electrical distribution network with PostGIS';
COMMENT ON TABLE grid.substations IS 'High and medium voltage substations';
COMMENT ON TABLE grid.transformers IS 'Distribution transformers (MV/LV)';
COMMENT ON TABLE grid.power_lines IS 'Transmission and distribution lines';
COMMENT ON TABLE grid.meters IS 'Smart meters (AMI)';
COMMENT ON TABLE grid.meter_readings IS 'Time-series meter readings';
