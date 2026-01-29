//! Microgrid zoning using K-Means clustering

use pyo3::prelude::*;
use std::collections::HashMap;

/// Zone information
#[pyclass]
#[derive(Debug, Clone)]
pub struct ZoneInfo {
    #[pyo3(get)]
    pub zone_id: i32,
    #[pyo3(get)]
    pub centroid_lat: f64,
    #[pyo3(get)]
    pub centroid_lon: f64,
    #[pyo3(get)]
    pub meter_count: i32,
    #[pyo3(get)]
    pub transformer_name: String,
}

#[pymethods]
impl ZoneInfo {
    #[new]
    pub fn new(zone_id: i32, centroid_lat: f64, centroid_lon: f64, meter_count: i32, transformer_name: String) -> Self {
        ZoneInfo { zone_id, centroid_lat, centroid_lon, meter_count, transformer_name }
    }
}

/// Simple K-Means clustering for zone assignment
#[pyclass]
#[derive(Debug, Clone)]
pub struct ZoningService {
    num_zones: usize,
    centroids: Vec<(f64, f64)>,
    zone_meters: HashMap<i32, Vec<String>>,
    transformer_names: Vec<String>,
}

impl ZoningService {
    fn find_nearest_centroid(&self, coord: &(f64, f64)) -> i32 {
        let mut min_dist = f64::MAX;
        let mut nearest = 0i32;
        
        for (i, centroid) in self.centroids.iter().enumerate() {
            let dist = self.haversine_distance(coord, centroid);
            if dist < min_dist {
                min_dist = dist;
                nearest = i as i32;
            }
        }
        
        nearest
    }
    
    fn haversine_distance(&self, p1: &(f64, f64), p2: &(f64, f64)) -> f64 {
        // Simplified Euclidean distance (good enough for small areas)
        let dlat = p1.0 - p2.0;
        let dlon = p1.1 - p2.1;
        (dlat * dlat + dlon * dlon).sqrt()
    }
    
    fn update_centroids(&mut self, coordinates: &[(f64, f64)], assignments: &[i32]) {
        for i in 0..self.num_zones {
            let mut sum_lat = 0.0;
            let mut sum_lon = 0.0;
            let mut count = 0;
            
            for (j, &zone) in assignments.iter().enumerate() {
                if zone == i as i32 {
                    sum_lat += coordinates[j].0;
                    sum_lon += coordinates[j].1;
                    count += 1;
                }
            }
            
            if count > 0 {
                self.centroids[i] = (sum_lat / count as f64, sum_lon / count as f64);
            }
        }
    }
    
    fn calculate_centroids(&mut self, coordinates: &[(f64, f64)], zone_ids: &[i32]) {
        self.centroids = vec![(0.0, 0.0); self.num_zones];
        let mut counts = vec![0; self.num_zones];
        
        for (coord, &zone_id) in coordinates.iter().zip(zone_ids.iter()) {
            let idx = (zone_id - 1) as usize;
            if idx < self.num_zones {
                self.centroids[idx].0 += coord.0;
                self.centroids[idx].1 += coord.1;
                counts[idx] += 1;
            }
        }
        
        for i in 0..self.num_zones {
            if counts[i] > 0 {
                self.centroids[i].0 /= counts[i] as f64;
                self.centroids[i].1 /= counts[i] as f64;
            }
        }
    }
}

#[pymethods]
impl ZoningService {
    #[new]
    #[pyo3(signature = (num_zones = 3))]
    pub fn new(num_zones: usize) -> Self {
        // Default transformer names
        let transformer_names: Vec<String> = (1..=num_zones)
            .map(|i| format!("Transformer_{}", i))
            .collect();
        
        ZoningService {
            num_zones,
            centroids: Vec::new(),
            zone_meters: HashMap::new(),
            transformer_names,
        }
    }
    
    /// Set custom transformer names
    pub fn set_transformer_names(&mut self, names: Vec<String>) {
        self.transformer_names = names;
    }
    
    /// Fit zones using K-Means clustering on coordinates
    /// Returns zone IDs (1-indexed) for each coordinate
    pub fn fit(&mut self, coordinates: Vec<(f64, f64)>) -> Vec<i32> {
        let n = coordinates.len();
        
        if n < self.num_zones {
            // Simple round-robin assignment
            let zone_ids: Vec<i32> = (0..n)
                .map(|i| ((i % self.num_zones) + 1) as i32)
                .collect();
            self.calculate_centroids(&coordinates, &zone_ids);
            return zone_ids;
        }
        
        // Initialize centroids using first N points spread across data
        let step = n / self.num_zones;
        self.centroids = (0..self.num_zones)
            .map(|i| coordinates[i * step])
            .collect();
        
        // K-Means iterations
        let max_iterations = 100;
        let mut assignments = vec![0i32; n];
        
        for _ in 0..max_iterations {
            let mut changed = false;
            
            // Assign each point to nearest centroid
            for (i, coord) in coordinates.iter().enumerate() {
                let nearest = self.find_nearest_centroid(coord);
                if assignments[i] != nearest {
                    assignments[i] = nearest;
                    changed = true;
                }
            }
            
            if !changed {
                break;
            }
            
            // Update centroids
            self.update_centroids(&coordinates, &assignments);
        }
        
        // Convert to 1-indexed
        let zone_ids: Vec<i32> = assignments.iter().map(|&z| z + 1).collect();
        
        zone_ids
    }
    
    /// Add meter to zone tracking
    pub fn add_meter(&mut self, zone_id: i32, meter_id: String) {
        self.zone_meters
            .entry(zone_id)
            .or_insert_with(Vec::new)
            .push(meter_id);
    }
    
    /// Get zone info for a specific zone
    pub fn get_zone_info(&self, zone_id: i32) -> Option<ZoneInfo> {
        let idx = (zone_id - 1) as usize;
        if idx >= self.num_zones {
            return None;
        }
        
        let (lat, lon) = if idx < self.centroids.len() {
            self.centroids[idx]
        } else {
            (0.0, 0.0)
        };
        
        let count = self.zone_meters
            .get(&zone_id)
            .map(|v| v.len() as i32)
            .unwrap_or(0);
        
        let name = self.transformer_names
            .get(idx)
            .cloned()
            .unwrap_or_else(|| format!("Transformer_{}", zone_id));
        
        Some(ZoneInfo::new(zone_id, lat, lon, count, name))
    }
    
    /// Get all zone summaries
    pub fn get_all_zones(&self) -> Vec<ZoneInfo> {
        (1..=self.num_zones as i32)
            .filter_map(|z| self.get_zone_info(z))
            .collect()
    }
    
    /// Get centroids
    pub fn get_centroids(&self) -> Vec<(f64, f64)> {
        self.centroids.clone()
    }
    
    /// Calculate wheeling charge between zones
    pub fn wheeling_charge(&self, from_zone: i32, to_zone: i32, amount_kwh: f64, same_zone_rate: f64, cross_zone_rate: f64) -> f64 {
        if from_zone == to_zone {
            same_zone_rate * amount_kwh
        } else {
            cross_zone_rate * amount_kwh
        }
    }
}
