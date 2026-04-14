/**
 * Electrical Grid Map Types
 * 
 * Types for visualizing Thai electrical infrastructure (EGAT, MEA, PEA)
 */

export interface ElectricalInfrastructure {
  id: string;
  type: InfrastructureType;
  operator: 'EGAT' | 'MEA' | 'PEA';
  latitude: number;
  longitude: number;
  voltage_kv?: number;
  name_en?: string;
  name_th?: string;
  status?: 'operational' | 'under_construction' | 'decommissioned';
  commissioning_year?: number;
  province?: string;
  district?: string;
  ref?: string;
  properties?: Record<string, any>;
}

export type InfrastructureType = 
  | 'transmission_substation'    // EGAT 500kV/230kV/115kV
  | 'distribution_substation'    // MEA/PEA 115kV/22kV
  | 'transmission_tower'         // EGAT transmission towers
  | 'distribution_pole'          // MEA/PEA poles
  | 'power_plant'                // EGAT generation
  | 'solar_farm'                 // Solar generation
  | 'battery_storage'            // Battery energy storage
  | 'ev_charging_station';       // EV charging

export interface InfrastructureLayer {
  id: string;
  type: InfrastructureType;
  operator: 'EGAT' | 'MEA' | 'PEA';
  visible: boolean;
  color: string;
  icon: string;
  minZoom: number;
}

export interface ElectricalGridFeatureCollection {
  type: 'FeatureCollection';
  features: ElectricalGridFeature[];
}

export interface ElectricalGridFeature {
  type: 'Feature';
  geometry: {
    type: 'Point' | 'LineString';
    coordinates: [number, number];
  };
  properties: ElectricalInfrastructure;
}

export interface ElectricalGridStats {
  totalInfrastructure: number;
  byOperator: {
    EGAT: number;
    MEA: number;
    PEA: number;
  };
  byType: Record<InfrastructureType, number>;
  byVoltage: {
    '500kV': number;
    '230kV': number;
    '115kV': number;
    '22kV': number;
    '33kV': number;
  };
  byProvince: Record<string, number>;
}

export interface FilterState {
  operators: ('EGAT' | 'MEA' | 'PEA')[];
  types: InfrastructureType[];
  voltageLevels: number[];
  provinces: string[];
  status: string[];
  searchQuery: string;
}

export const DEFAULT_FILTERS: FilterState = {
  operators: ['EGAT', 'MEA', 'PEA'],
  types: [
    'transmission_substation',
    'distribution_substation',
    'transmission_tower',
    'distribution_pole',
    'power_plant',
    'solar_farm',
    'battery_storage',
    'ev_charging_station'
  ],
  voltageLevels: [],
  provinces: [],
  status: ['operational'],
  searchQuery: ''
};

export const INFRASTRUCTURE_LAYERS: InfrastructureLayer[] = [
  {
    id: 'egat_transmission_substation',
    type: 'transmission_substation',
    operator: 'EGAT',
    visible: true,
    color: '#EF4444',  // Red
    icon: 'substation',
    minZoom: 6
  },
  {
    id: 'mea_distribution_substation',
    type: 'distribution_substation',
    operator: 'MEA',
    visible: true,
    color: '#3B82F6',  // Blue
    icon: 'substation',
    minZoom: 8
  },
  {
    id: 'pea_distribution_substation',
    type: 'distribution_substation',
    operator: 'PEA',
    visible: true,
    color: '#10B981',  // Green
    icon: 'substation',
    minZoom: 8
  },
  {
    id: 'egat_transmission_tower',
    type: 'transmission_tower',
    operator: 'EGAT',
    visible: true,
    color: '#F59E0B',  // Amber
    icon: 'tower',
    minZoom: 10
  },
  {
    id: 'mea_distribution_pole',
    type: 'distribution_pole',
    operator: 'MEA',
    visible: true,
    color: '#60A5FA',  // Light Blue
    icon: 'pole',
    minZoom: 12
  },
  {
    id: 'pea_distribution_pole',
    type: 'distribution_pole',
    operator: 'PEA',
    visible: true,
    color: '#34D399',  // Light Green
    icon: 'pole',
    minZoom: 12
  },
  {
    id: 'power_plant',
    type: 'power_plant',
    operator: 'EGAT',
    visible: true,
    color: '#8B5CF6',  // Purple
    icon: 'plant',
    minZoom: 6
  },
  {
    id: 'solar_farm',
    type: 'solar_farm',
    operator: 'EGAT',
    visible: true,
    color: '#FBBF24',  // Amber
    icon: 'solar',
    minZoom: 8
  },
  {
    id: 'battery_storage',
    type: 'battery_storage',
    operator: 'EGAT',
    visible: true,
    color: '#EC4899',  // Pink
    icon: 'battery',
    minZoom: 8
  },
  {
    id: 'ev_charging_station',
    type: 'ev_charging_station',
    operator: 'MEA',
    visible: true,
    color: '#06B6D4',  // Cyan
    icon: 'ev',
    minZoom: 10
  }
];

export const OPERATOR_INFO = {
  EGAT: {
    name: 'Electricity Generating Authority of Thailand',
    name_th: 'การไฟฟ้าฝ่ายผลิตแห่งประเทศไทย',
    wikidata: 'Q5353891',
    service_area: 'National (Transmission)',
    color: '#EF4444'
  },
  MEA: {
    name: 'Metropolitan Electricity Authority',
    name_th: 'การไฟฟ้านครหลวง',
    wikidata: 'Q13116849',
    service_area: 'Bangkok, Nonthaburi, Samut Prakan',
    color: '#3B82F6'
  },
  PEA: {
    name: 'Provincial Electricity Authority',
    name_th: 'การไฟฟ้าส่วนภูมิภาค',
    wikidata: 'Q7385915',
    service_area: 'All other provinces',
    color: '#10B981'
  }
};
