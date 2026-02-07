export interface Reading {
    meter_id: string;
    meter_type: string;
    location: string;
    energy_generated: number;
    energy_consumed: number;
    surplus_energy: number;
    deficit_energy: number;
    battery_level: number;
    temperature: number;
    weather_condition: string;
    rec_eligible: boolean;
    carbon_offset: number;
    max_sell_price?: number;
    max_buy_price?: number;
}
