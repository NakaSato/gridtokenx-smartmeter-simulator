from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request
from .dependencies import get_engine

router = APIRouter(prefix="/meters", tags=["Meters"])

@router.get("")
async def list_meters(engine=Depends(get_engine)):
    """Get list of all meters with their serial numbers"""
    meters_list = []
    for meter in engine.meters:
        meters_list.append({
            "meter_id": meter.meter_id,
            "serial_number": meter.meter_id,
            "meter_type": meter.config.get('meter_type', 'unknown'),
            "location": meter.config.get('location', 'Unknown'),
            "status": "active"
        })
    
    return {
        "meters": meters_list,
        "count": len(meters_list)
    }

@router.get("/{meter_id}")
async def get_meter(meter_id: str, engine=Depends(get_engine)):
    """Get details of a specific meter by serial number"""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    
    return {
        "meter_id": meter.meter_id,
        "serial_number": meter.meter_id,
        "meter_type": meter.config.get('meter_type', 'unknown'),
        "location_name": meter.config.get('location_name', meter.config.get('location', 'Unknown')),
        "location": meter.config.get('location', 'Unknown'),
        "latitude": meter.config.get('latitude'),
        "longitude": meter.config.get('longitude'),
        "phase": meter.config.get('phase'),
        "solar_capacity": meter.config.get('solar_capacity', 0),
        "has_battery": meter.config.get('has_battery', False),
        "has_solar": meter.config.get('has_solar', False),
        "wallet_address": meter.config.get('wallet_address'),
        "status": "active"
    }

from pydantic import BaseModel
from typing import Optional

class MeterCreateRequest(BaseModel):
    meter_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    solar_capacity: Optional[float] = 0.0
    trading_preference: Optional[str] = "moderate"
    custom_id: Optional[str] = None
    wallet_address: Optional[str] = None

@router.post("")
async def create_meter(meter_data: MeterCreateRequest, engine=Depends(get_engine)):
    """Dynamically add a new meter to the simulation."""
    try:
        from ..core.meter import SmartMeter
        meter_id = meter_data.custom_id or f"METER-{len(engine.meters) + 1:04d}"
        
        config = {
            "meter_id": meter_id,
            "meter_type": meter_data.meter_type,
            "location": meter_data.location,
            "latitude": meter_data.latitude,
            "longitude": meter_data.longitude,
            "solar_capacity": meter_data.solar_capacity,
            "wallet_address": meter_data.wallet_address,
        }
        
        new_meter = SmartMeter(config)
        await engine.add_meter(new_meter)
        
        return {
            "success": True, 
            "message": f"Meter {meter_id} added successfully",
            "meter": {
                "meter_id": new_meter.meter_id,
                "type": new_meter.config['meter_type']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MeterOverrideRequest(BaseModel):
    gen: Optional[float] = None
    cons: Optional[float] = None

@router.post("/{meter_id}/override")
async def override_meter(meter_id: str, data: MeterOverrideRequest, engine=Depends(get_engine)):
    """Manually override generation and consumption for a meter."""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")
    
    if data.gen is not None:
        meter.manual_override_gen = data.gen
    if data.cons is not None:
        meter.manual_override_cons = data.cons
        
    return {
        "success": True,
        "message": f"Overrides applied to {meter_id}",
        "overrides": {
            "gen": getattr(meter, 'manual_override_gen', None),
            "cons": getattr(meter, 'manual_override_cons', None)
        }
    }

from ..core.billing import TransactionType

@router.get("/{meter_id}/history")
async def get_meter_history(meter_id: str, limit: int = 100, engine=Depends(get_engine)):
    """Get historical energy transactions for a specific meter."""
    if meter_id not in engine.billing_engines:
        # Fallback to empty history if billing engine not started for this meter yet
        return {"history": [], "count": 0, "stats": {"total_gen_kwh": 0, "total_cons_kwh": 0}}
    
    billing_engine = engine.billing_engines[meter_id]
    # Return last N transactions
    txs = billing_engine.transactions[-limit:]
    
    # Calculate aggregated stats using billing engine transaction types
    # Generation: grid_export + p2p_sell
    total_gen = sum(
        tx.energy_kwh for tx in txs 
        if tx.transaction_type in [TransactionType.GRID_EXPORT, TransactionType.P2P_SELL]
    )
    
    # Consumption: grid_purchase + p2p_buy
    total_cons = sum(
        tx.energy_kwh for tx in txs 
        if tx.transaction_type in [TransactionType.GRID_PURCHASE, TransactionType.P2P_BUY]
    )
    
    # Solar Self-Consumption (optional but useful for some metrics)
    total_solar_self = sum(
        tx.energy_kwh for tx in txs 
        if tx.transaction_type == TransactionType.SOLAR_SELF_CONSUMPTION
    )
    
    # Financial Summary
    total_revenue = sum(tx.total_baht for tx in txs if tx.transaction_type in [TransactionType.GRID_EXPORT, TransactionType.P2P_SELL, TransactionType.SOLAR_SELF_CONSUMPTION])
    total_cost = sum(tx.total_baht for tx in txs if tx.transaction_type in [TransactionType.GRID_PURCHASE, TransactionType.P2P_BUY])

    return {
        "meter_id": meter_id,
        "history": [
            {
                "timestamp": tx.timestamp.isoformat(),
                "type": tx.transaction_type.value,
                "amount_kwh": tx.energy_kwh,
                "price": tx.price_baht_kwh,
                "total": tx.total_baht,
                "counterparty": tx.counterparty_id,
                "is_p2p": tx.transaction_type in [TransactionType.P2P_BUY, TransactionType.P2P_SELL]
            } for tx in txs
        ],
        "stats": {
            "total_gen_kwh": total_gen,
            "total_cons_kwh": total_cons,
            "total_solar_self_kwh": total_solar_self,
            "p2p_participation_kwh": sum(tx.energy_kwh for tx in txs if tx.transaction_type in [TransactionType.P2P_BUY, TransactionType.P2P_SELL]),
            "total_revenue_baht": total_revenue,
            "total_cost_baht": total_cost,
            "net_financial_baht": total_revenue - total_cost
        },
        "count": len(txs)
    }

@router.get("/{meter_id}/wallet")
async def get_meter_wallet(meter_id: str, engine=Depends(get_engine)):
    """Get multi-token wallet balances for a specific meter."""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # Get simulated balances from engine
    summary = engine.settlement.get_wallet_summary(meter_id)
    
    # Check for real on-chain balances if wallet address is available
    wallet_address = meter.config.get('wallet_address')
    if wallet_address:
        try:
            import aiohttp
            # Default to localhost:4000 (API Gateway)
            gateway_url = engine.config.get('api_gateway_url', 'http://localhost:4000')
            url = f"{gateway_url}/api/v1/wallets/{wallet_address}/balance"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2.0) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Bridge real balances into simulation summary
                        summary["onchain_grx"] = data.get("grx_balance", 0.0)
                        summary["onchain_sol"] = data.get("sol_balance", 0.0)
                        summary["is_synced_with_solana"] = True
                        summary["blockchain_address"] = wallet_address
                    else:
                        summary["is_synced_with_solana"] = False
                        summary["sync_error"] = f"Gateway returned {response.status}"
        except Exception as e:
            summary["is_synced_with_solana"] = False
            summary["sync_error"] = str(e)
            
    return summary

@router.post("/{meter_id}/airdrop")
async def airdrop_sol(meter_id: str, engine=Depends(get_engine)):
    """Airdrop 1.0 SOL and 1000 THB to a meter for simulation testing."""
    meter = next((m for m in engine.meters if m.meter_id == meter_id), None)
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # 1. Update local simulated balance
    acc = engine.settlement.get_account(meter_id)
    acc.sol_balance += 1.0
    acc.thb_balance += 1000.0
    
    # 2. Trigger real on-chain airdrop/faucet if wallet is linked
    wallet_address = meter.config.get('wallet_address')
    onchain_success = False
    onchain_message = "No wallet linked for on-chain airdrop"
    sol_tx_signature = None
    token_tx_signature = None
    
    if wallet_address:
        try:
            import aiohttp
            from ..config import get_config
            gateway_url = get_config().api_gateway_url
            url = f"{gateway_url}/api/v1/dev/faucet"
            
            payload = {
                "wallet_address": wallet_address,
                "amount_sol": 1.0,
                "deposit_fiat": 1000.0,
                "mint_tokens_kwh": 10.0  # Also mint some tokens for testing
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10.0) as response:
                    if response.status in (200, 201):
                        onchain_success = True
                        data = await response.json()
                        onchain_message = data.get("message", "Success")
                        sol_tx_signature = data.get("sol_tx_signature")
                        token_tx_signature = data.get("token_tx_signature")
                    else:
                        onchain_message = f"Gateway error: {response.status}"
        except Exception as e:
            onchain_message = f"Connection failed: {str(e)}"
    
    return {
        "success": True, 
        "local_sol_balance": acc.sol_balance,
        "local_thb_balance": acc.thb_balance,
        "onchain_sync": onchain_success,
        "onchain_message": onchain_message,
        "sol_tx_signature": sol_tx_signature,
        "token_tx_signature": token_tx_signature,
        "message": f"Successfully funded {meter_id}"
    }

@router.get("/{meter_id}/billing-history")
async def get_meter_billing_history(meter_id: str, engine=Depends(get_engine)):
    """Get summary of past monthly bills for a specific meter."""
    if meter_id not in engine.billing_engines:
        return {"history": [], "count": 0}
    
    billing_engine = engine.billing_engines[meter_id]
    current_time = engine.current_sim_time
    
    # Generate history for the last 6 months (simulated)
    history = []
    for i in range(1, 7):
        # Calculate past month/year
        m = current_time.month - i
        y = current_time.year
        if m <= 0:
            m += 12
            y -= 1
        
        try:
            bill = billing_engine.generate_monthly_bill(m, y)
            if bill.grid_consumption_kwh > 0 or bill.solar_generation_kwh > 0:
                history.append({
                    "month": m,
                    "year": y,
                    "total_kwh": bill.grid_consumption_kwh + bill.p2p_purchase_kwh + bill.solar_self_consumption_kwh,
                    "net_amount": bill.net_amount_baht,
                    "carbon_saved": bill.carbon_saved_kg,
                    "status": "paid"
                })
        except Exception:
            continue
            
    return {
        "meter_id": meter_id,
        "history": history,
        "count": len(history)
    }
