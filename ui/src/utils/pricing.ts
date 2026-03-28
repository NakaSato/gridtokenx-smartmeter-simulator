/**
 * Thai utility rates (PEA/MEA typical rates for residential 1.1.2)
 */
export const UTILITY_RATES = {
    energy: [
        { limit: 15, rate: 2.5244 },    // 0-15 kWh
        { limit: 25, rate: 3.2484 },    // 16-25 kWh
        { limit: 35, rate: 3.9428 },    // 26-35 kWh
        { limit: 50, rate: 4.2377 },    // 36-50 kWh
        { limit: 100, rate: 4.4061 },   // 51-100 kWh
        { limit: 200, rate: 4.7218 },   // 101-200 kWh
        { limit: 300, rate: 4.8294 },   // 201-300 kWh
        { limit: 400, rate: 5.0405 },   // 301-400 kWh
        { limit: Infinity, rate: 5.3201 }, // 401+ kWh
    ],
    ftRate: 0.0972,  // Ft charge per kWh
    serviceCharge: 8.19,  // Monthly service charge
    vatRate: 0.07,  // 7% VAT
};

export interface PriceBreakdown {
    energyCharge: number;
    ftCharge: number;
    serviceCharge: number;
    totalBeforeVat: number;
    vat: number;
    totalAmount: number;
    averageRate: number;
}

/**
 * Calculates utility price for a given consumption in kWh
 */
export const calculateUtilityPrice = (consumptionKwh: number): PriceBreakdown => {
    let energyCharge = 0;
    let remaining = consumptionKwh;
    let previousLimit = 0;

    for (const tier of UTILITY_RATES.energy) {
        const tierSize = tier.limit - previousLimit;
        const consumptionInTier = Math.min(remaining, tierSize);
        energyCharge += consumptionInTier * tier.rate;
        remaining -= consumptionInTier;
        previousLimit = tier.limit;

        if (remaining <= 0) break;
    }

    const ftCharge = consumptionKwh * UTILITY_RATES.ftRate;
    const totalBeforeVat = energyCharge + ftCharge + UTILITY_RATES.serviceCharge;
    const vat = totalBeforeVat * UTILITY_RATES.vatRate;
    const totalAmount = totalBeforeVat + vat;
    const averageRate = consumptionKwh > 0 ? totalAmount / consumptionKwh : 0;

    return {
        energyCharge,
        ftCharge,
        serviceCharge: UTILITY_RATES.serviceCharge,
        totalBeforeVat,
        vat,
        totalAmount,
        averageRate,
    };
};
