# Market Engine Architecture

**Location:** [`src/smart_meter_simulator/core/market.py`](../src/smart_meter_simulator/core/market.py)

This document describes the P2P market engine, pricing mechanisms, and settlement.

## Components Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Market Engine                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Order      │  │   Matching   │  │  Settlement  │     │
│  │   Book       │  │   Engine     │  │   Engine     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Double     │  │     LMP      │  │    Thai      │     │
│  │   Auction    │  │  Calculation │  │   Tariff     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

## Market Model

### Double Auction Mechanism

```python
class DoubleAuction:
    """
    Double auction market mechanism.
    
    Features:
    - Buyers submit bids (price, quantity)
    - Sellers submit asks (price, quantity)
    - Clearing price = intersection of supply/demand
    - Uniform pricing (all trades at clearing price)
    
    Matching Algorithm:
    1. Sort bids (descending)
    2. Sort asks (ascending)
    3. Find intersection
    4. Execute trades at clearing price
    """
```

### Order Types

```python
class MarketOrder:
    """Market order representation."""
    
    order_id: str
    meter_id: str
    order_type: Literal['BUY', 'SELL']
    price_baht_kwh: float
    quantity_kwh: float
    timestamp: datetime
    status: Literal['PENDING', 'MATCHED', 'FILLED', 'CANCELLED']
```

## Pricing Mechanisms

### Dynamic P2P Pricing

```python
def calculate_dynamic_price(self, supply: float, demand: float) -> float:
    """
    Calculate dynamic P2P price based on supply/demand.
    
    Formula:
    p_t = arctan(e^D_t) + arctan(R_t)/10 + p_min
    
    Where:
    - D_t = (Demand - Supply) / 100  (normalized difference)
    - R_t = Demand / Supply           (ratio)
    - p_min = 2.20 Baht/kWh           (price floor)
    
    Characteristics:
    - Balanced (S=D=100): ~3.06 Baht/kWh
    - High Demand (S=50, D=150): ~3.5-4.5 Baht/kWh
    - Oversupply (S=200, D=50): ~2.0-2.5 Baht/kWh
    - Scarcity (S=0, D=100): 3.30 Baht/kWh (1.5× base)
    """
    if supply == 0:
        return self.base_price * 1.5  # Scarcity pricing
    
    D_t = (demand - supply) / 100.0
    R_t = demand / supply
    
    price = (
        math.arctan(math.exp(D_t)) +
        math.arctan(R_t) / 10.0 +
        self.price_floor
    )
    
    return price
```

### Locational Marginal Pricing (LMP)

```python
class LMPCalculator:
    """
    Locational Marginal Price calculation.
    
    Components:
    LMP = LMP_energy + LMP_congestion + LMP_losses
    
    Where:
    - LMP_energy: System marginal energy cost
    - LMP_congestion: Congestion cost due to transmission limits
    - LMP_losses: Cost of transmission losses
    
    Calculation:
    1. Run optimal power flow (OPF)
    2. Extract Lagrange multipliers (λ)
    3. LMP_i = λ_i at bus i
    """
```

### LMP Implementation

```python
def calculate_lmp(self, net, load_profile, gen_profile):
    """
    Calculate nodal prices based on grid congestion.
    
    Process:
    1. Run DC optimal power flow (DC-OPF)
    2. Extract dual variables (λ) for power balance constraints
    3. LMP at each bus = λ + μ × PTDF
    
    Where:
    - λ: System lambda (marginal cost)
    - μ: Congestion shadow price
    - PTDF: Power Transfer Distribution Factor
    
    Returns:
        Dict mapping bus_id → LMP (Baht/kWh)
    """
    # Run DC-OPF
    ppf_result = pp.rundcopp(net)
    
    # Extract system lambda
    system_lambda = pp.get_lambda(net)
    
    # Calculate congestion component
    congestion = self.calculate_congestion_cost(net, ppf_result)
    
    # Calculate LMP per bus
    lmp = {}
    for bus in net.bus.index:
        lmp[bus] = system_lambda + congestion.get(bus, 0.0)
    
    return lmp
```

## Thai Tariff Integration

### TOU Tariff Structure

```python
class ThaiTOUTariff:
    """
    Thai Time-of-Use tariff structure.
    
    Categories (2026):
    - Type 1.1.2: Standard residential (>150 kWh/month)
    - Type 1.2: Time-of-Use (optional)
    - Type 2.2: Small business
    
    Rates (Type 1.2, <22 kV):
    - On-Peak: 5.7982 Baht/kWh (Mon-Fri 09:00-22:00)
    - Off-Peak: 2.6369 Baht/kWh (Mon-Fri 22:00-09:00, weekends)
    - Service Charge: 33.29 Baht/month
    """
```

### Ladder Tariff Calculation

```python
def calculate_ladder_tariff(self, consumption_kwh: float) -> float:
    """
    Calculate bill using Thai ladder tariff (Type 1.1.2).
    
    Tiers:
    - 0-150 kWh: 3.2484 Baht/kWh
    - 151-400 kWh: 4.2218 Baht/kWh
    - >400 kWh: 4.4217 Baht/kWh
    
    Additional Charges:
    - Ft (Jan-Apr 2026): 0.0972 Baht/kWh
    - Service Charge: 24.62 Baht/month
    - VAT: 7%
    
    Example:
    consumption = 500 kWh
    
    Tier 1: 150 × 3.2484 = 487.26
    Tier 2: 250 × 4.2218 = 1055.45
    Tier 3: 100 × 4.4217 = 442.17
    
    Subtotal: 1984.88
    Ft: 500 × 0.0972 = 48.60
    Service: 24.62
    
    Total (before VAT): 2058.10
    VAT (7%): 144.07
    
    Grand Total: 2202.17 Baht
    """
    tiers = [
        (150, 3.2484),
        (250, 4.2218),  # 151-400
        (float('inf'), 4.4217)  # >400
    ]
    
    total = 0.0
    remaining = consumption_kwh
    
    for limit, rate in tiers:
        if remaining <= 0:
            break
        usage = min(remaining, limit)
        total += usage * rate
        remaining -= limit
    
    # Add Ft charge
    total += consumption_kwh * 0.0972
    
    # Add service charge
    total += 24.62
    
    # Apply VAT
    total *= 1.07
    
    return total
```

### Wheeling Cost

```python
WHEELING_COSTS = {
    'residential': 1.76,      # Baht/kWh (average)
    'commercial': 1.50,       # Baht/kWh
    'industrial': 1.30,       # Baht/kWh
}

def calculate_p2p_transaction_cost(
    quantity_kwh: float,
    p2p_price: float,
    wheeling_rate: float = 1.76
) -> dict:
    """
    Calculate total P2P transaction cost.
    
    Components:
    - Energy cost: quantity × p2p_price
    - Wheeling cost: quantity × wheeling_rate
    
    Example:
    quantity = 50 kWh
    p2p_price = 3.50 Baht/kWh
    wheeling = 1.76 Baht/kWh
    
    Energy: 50 × 3.50 = 175.00
    Wheeling: 50 × 1.76 = 88.00
    Total: 263.00 Baht
    """
    energy_cost = quantity_kwh * p2p_price
    wheeling_cost = quantity_kwh * wheeling_rate
    
    return {
        'energy_cost': energy_cost,
        'wheeling_cost': wheeling_cost,
        'total_cost': energy_cost + wheeling_cost
    }
```

## Market Clearing

### Order Matching

```python
def match_orders(self, buy_orders, sell_orders):
    """
    Match buy and sell orders via double auction.
    
    Algorithm:
    1. Sort buy orders (descending price)
    2. Sort sell orders (ascending price)
    3. Find clearing price where supply = demand
    4. Execute trades at clearing price
    
    Returns:
        List of matched trades
    """
    # Sort orders
    buy_orders.sort(key=lambda x: x.price, reverse=True)
    sell_orders.sort(key=lambda x: x.price)
    
    trades = []
    remaining_buy = buy_orders.copy()
    remaining_sell = sell_orders.copy()
    
    # Match orders
    for buy in buy_orders:
        for sell in sell_orders:
            if buy.price >= sell.price:  # Price overlap
                # Determine trade quantity
                quantity = min(buy.remaining, sell.remaining)
                
                # Create trade at clearing price
                clearing_price = (buy.price + sell.price) / 2
                
                trade = Trade(
                    buyer=buy.meter_id,
                    seller=sell.meter_id,
                    quantity=quantity,
                    price=clearing_price
                )
                trades.append(trade)
                
                # Update remaining quantities
                buy.remaining -= quantity
                sell.remaining -= quantity
                
                if buy.remaining == 0:
                    break
    
    return trades
```

### Market Clearing Result

```python
class MarketClearingResult:
    """Market clearing result."""
    
    timestamp: datetime
    clearing_price: float
    total_volume_kwh: float
    trades: List[Trade]
    unmatched_buy: List[Order]
    unmatched_sell: List[Order]
    lmp_by_bus: Dict[int, float]
```

## Settlement Engine

**Location:** [`src/smart_meter_simulator/core/settlement.py`](../src/smart_meter_simulator/core/settlement.py)

### Settlement Process

```python
class SettlementEngine:
    """
    Settlement engine for market transactions.
    
    Process:
    1. Validate trades
    2. Calculate payments
    3. Update balances
    4. Record transactions
    
    Integration:
    - Solana blockchain for tokenized settlement
    - REC (Renewable Energy Certificate) generation
    - Carbon credit tracking
    """
```

### Payment Calculation

```python
def calculate_settlement(self, trades: List[Trade]) -> dict:
    """
    Calculate net settlements for all participants.
    
    For each participant:
    - Net payment = Σ(buys) - Σ(sells)
    - Positive = owes money (buyer)
    - Negative = receives money (seller)
    
    Returns:
        Dict mapping meter_id → net_payment
    """
    settlements = defaultdict(float)
    
    for trade in trades:
        payment = trade.quantity * trade.price
        
        # Buyer pays
        settlements[trade.buyer] += payment
        
        # Seller receives
        settlements[trade.seller] -= payment
    
    return dict(settlements)
```

## Carbon Tracking

### REC Generation

```python
class RECCertification:
    """
    Renewable Energy Certificate generation.
    
    Parameters:
    - 1 REC = 1 MWh renewable generation
    - Certification via university validator
    - Blockchain-based tracking
    
    Integration:
    - Engineering department authority
    - REC certification endpoint
    - Carbon offset rate: 0.7
    """
```

### Carbon Intensity

```python
def calculate_carbon_intensity(self, generation_mix: dict) -> float:
    """
    Calculate grid carbon intensity.
    
    Generation Mix:
    - Solar: 0 gCO2/kWh
    - Wind: 0 gCO2/kWh
    - Natural Gas: 400 gCO2/kWh
    - Coal: 800 gCO2/kWh
    
    Returns:
        Carbon intensity (gCO2/kWh)
    """
    carbon_factors = {
        'solar': 0,
        'wind': 0,
        'gas': 400,
        'coal': 800
    }
    
    total_carbon = 0
    total_generation = 0
    
    for source, generation in generation_mix.items():
        total_carbon += generation * carbon_factors.get(source, 0)
        total_generation += generation
    
    return total_carbon / total_generation if total_generation > 0 else 0
```

## Market Analytics

### Supply/Demand Analysis

```python
class MarketAnalytics:
    """
    Market analytics and reporting.
    
    Metrics:
    - Supply/demand ratio
    - Price elasticity
    - Market concentration (HHI)
    - Trading volume
    - Price volatility
    """
```

### Price Statistics

```python
def calculate_price_statistics(self, prices: List[float]) -> dict:
    """Calculate market price statistics."""
    return {
        'mean': np.mean(prices),
        'median': np.median(prices),
        'std': np.std(prices),
        'min': np.min(prices),
        'max': np.max(prices),
        'volatility': np.std(prices) / np.mean(prices)
    }
```

## Testing

```python
@pytest.mark.market
def test_dynamic_pricing(market_engine):
    # Balanced market
    price = market_engine.calculate_dynamic_price(100, 100)
    assert 3.0 <= price <= 3.2
    
    # High demand
    price = market_engine.calculate_dynamic_price(50, 150)
    assert price > 3.5
    
    # Oversupply
    price = market_engine.calculate_dynamic_price(200, 50)
    assert price < 2.5

@pytest.mark.market
def test_order_matching(market_engine):
    buy_orders = [MarketOrder(type='BUY', price=4.0, quantity=10)]
    sell_orders = [MarketOrder(type='SELL', price=3.0, quantity=10)]
    
    trades = market_engine.match_orders(buy_orders, sell_orders)
    
    assert len(trades) == 1
    assert trades[0].quantity == 10
    assert 3.0 <= trades[0].price <= 4.0
```

## Related Documents

- [System Overview](overview.md)
- [Economic Models Reference](../reference/economic-models.md)
- [Thai Tariffs Reference](../reference/thai-tariffs.md)
