export function calculateUtilityPrice(kwh: number): number {
    if (kwh <= 0) return 0;
    if (kwh <= 150) return kwh * 3.2484;
    if (kwh <= 400) return 150 * 3.2484 + (kwh - 150) * 4.2218;
    return 150 * 3.2484 + 250 * 4.2218 + (kwh - 400) * 4.4217;
}
