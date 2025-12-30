
import logging
import time
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Qiskit Imports
from qiskit_algorithms import QAOA, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA, SPSA
from qiskit_aer.primitives import Sampler
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer, CplexOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo

logger = logging.getLogger(__name__)

@dataclass
class TradeMatch:
    buyer_id: str
    seller_id: str
    amount_kwh: float
    price_per_kwh: float
    total_cost: float
    score: float  # The objective function value contribution

class QuantumOptimizer:
    """
    Quantum-Enhanced Optimizer for P2P Energy Trading.
    
    Uses QAOA (Quantum Approximate Optimization Algorithm) to solve the combinatorial
    optimization problem of matching buyers and sellers to maximize social welfare.
    """

    def __init__(self, use_quantum: bool = True):
        self.use_quantum = use_quantum
        
        # Configure Quantum Backend
        self.optimizer = COBYLA(maxiter=25) 
        self.sampler = Sampler(run_options={"shots": 128})
        
        # Using QAOA - standard for combinatorial optimization
        self.vqe = QAOA(sampler=self.sampler, optimizer=self.optimizer, reps=1)
        
        # The Optimizer Wrapper that handles QUBO conversion
        self.meo = MinimumEigenOptimizer(self.vqe)
        
        # Fallback classical solver (exact) for verification or fallback
        self.classical_optimizer = NumPyMinimumEigensolver()
        self.classical_meo = MinimumEigenOptimizer(self.classical_optimizer)

        logger.info(f"QuantumOptimizer initialized. Mode: {'Quantum (VQE)' if use_quantum else 'Classical (Exact)'}")

    def optimize_matches(
        self, 
        bids: List[Dict[str, Any]], 
        asks: List[Dict[str, Any]],
        cost_callback: Any, # Function(buyer_zone, seller_zone, amount) -> cost
        zone_voltages: Dict[str, float] = None # Map zone_id/meter_zone -> voltage (pu)
    ) -> Tuple[List[TradeMatch], Dict[str, Any]]:
        """
        Finds the optimal set of matches between buyers (bids) and sellers (asks).
        """
        start_time = time.time()
        
        # 1. Pre-filtering: Limit problem size for VQE simulation
        # Current quantum simulators struggle with > 16-20 qubits.
        # Each potential match is a binary variable.
        # We select top 3 Buyers and top 3 Sellers -> 9 variables (manageable).
        
        # Sort by urgency/price to pick best candidates
        sorted_bids = sorted(bids, key=lambda x: x['price'], reverse=True)[:3]
        sorted_asks = sorted(asks, key=lambda x: x['price'])[:3]
        
        if not sorted_bids or not sorted_asks:
            return [], {"status": "no_participants"}

        # 2. Construct Quadratic Program
        qp = QuadraticProgram()
        
        # Variables: x_i_j = 1 if buyer i matches seller j
        vars_map = {}
        for i, bid in enumerate(sorted_bids):
            for j, ask in enumerate(sorted_asks):
                var_name = f"x_{i}_{j}"
                qp.binary_var(var_name)
                vars_map[var_name] = (i, j)
        
        # Objective: Maximize Social Welfare = Sum( (BidPrice - AskPrice - NetworkCost) * Amount * x_ij )
        # We assume for matching that amount is the min(bid_amount, ask_amount) or fixed block.
        # To simplify QUBO, we treat it as "Matching 1 unit" or "Matching full available overlap"
        # Since x_ij is binary, we are deciding "Do they trade?".
        
        linear_terms = {}
        
        for i, bid in enumerate(sorted_bids):
            for j, ask in enumerate(sorted_asks):
                var_name = f"x_{i}_{j}"
                
                # Determine feasible trade amount
                amount = min(bid['amount'], ask['amount'])
                
                # Calculate Costs
                # cost_result = transaction_cost... (we approximate/call service)
                # Network Cost (Wheeling + Loss) per kWh
                # We need the unit cost.
                # Assuming cost_callback returns total cost for the amount.
                
                # We need separate components: Energy Cost vs Network Cost.
                # Welfare = (BuyerValue - SellerCost - NetworkCost)
                # BuyerValue = BidPrice * Amount
                # SellerCost = AskPrice * Amount
                # NetworkCost = calculated
                
                # We use the midpoint price or just the spread for Welfare
                # Welfare = (BidPrice - AskPrice) * Amount - NetworkFees
                
                # Estimate Network Fees:
                network_cost_obj = cost_callback(bid['zone'], ask['zone'], amount)
                # network_cost_obj.total_cost includes energy.
                # We want just the "friction" (wheeling + loss).
                # friction = wheeling_charge + loss_cost
                friction = network_cost_obj.wheeling_charge + network_cost_obj.loss_cost
                
                # --- Grid Stability Incentives ---
                # Default penalty if no voltage data
                stability_bonus = 0.0
                
                if zone_voltages:
                    # Seller (Generation): Good if Voltage < 0.95 (Under-voltage)
                    # Bad if Voltage > 1.05 (Over-voltage)
                    v_seller = zone_voltages.get(ask['zone'], 1.0)
                    v_buyer = zone_voltages.get(bid['zone'], 1.0)
                    
                    # Coefficients
                    COEFF_STABILITY = 5.0 # THB equivalent bonus per unit deviation
                    
                    # Seller Logic
                    if v_seller < 0.96:
                        stability_bonus += COEFF_STABILITY # We want more generation here
                    elif v_seller > 1.04:
                        stability_bonus -= COEFF_STABILITY # Reduce generation
                        
                    # Buyer Logic (Load)
                    if v_buyer > 1.04:
                         stability_bonus += COEFF_STABILITY # We want more load (charge EV etc)
                    elif v_buyer < 0.96:
                         stability_bonus -= COEFF_STABILITY # Reduce load
                
                welfare = (bid['price'] * amount) - (ask['price'] * amount) - friction + stability_bonus
                
                # In Qiskit QP, we Minimize. So we Maximize Welfare => Minimize (-Welfare)
                linear_terms[var_name] = -welfare

        qp.minimize(linear=linear_terms)

        # Constraints: 
        # 1. Each Buyer matches at most 1 Seller (Capacity constraint simplication)
        # Sum_j(x_ij) <= 1  forall i
        for i in range(len(sorted_bids)):
            indices = [f"x_{i}_{j}" for j in range(len(sorted_asks))]
            qp.linear_constraint(linear={name: 1 for name in indices}, sense='LE', rhs=1, name=f"buyer_{i}_limit")

        # 2. Each Seller matches at most 1 Buyer
        # Sum_i(x_ij) <= 1 forall j
        for j in range(len(sorted_asks)):
            indices = [f"x_{i}_{j}" for i in range(len(sorted_bids))]
            qp.linear_constraint(linear={name: 1 for name in indices}, sense='LE', rhs=1, name=f"seller_{j}_limit")

        # 3. Solve
        try:
            if self.use_quantum:
                result = self.meo.solve(qp)
            else:
                result = self.classical_meo.solve(qp)
        except Exception as e:
            logger.error(f"Quantum optimization failed: {e}. Falling back to Classical Exact Solver.")
            try:
                result = self.classical_meo.solve(qp)
                self.use_quantum = False # Disable for future runs to save time
            except Exception as e2:
                logger.error(f"Classical fallback failed: {e2}")
                return [], {"error": str(e)}

        # 4. Parse Results
        matches = []
        
        # result.x contains variable values
        if result.x is None:
             return [], {"status": "no_solution"}
             
        for var_name, val in result.variables_dict.items():
            if val > 0.9: # Binary 1
                i, j = vars_map[var_name]
                bid = sorted_bids[i]
                ask = sorted_asks[j]
                
                amount = min(bid['amount'], ask['amount'])
                
                # Re-calculate exact stats for the record
                network_cost_obj = cost_callback(bid['zone'], ask['zone'], amount)
                friction = network_cost_obj.wheeling_charge + network_cost_obj.loss_cost
                
                # Clearing Price: (Bid + Ask) / 2  (Simple mechanics)
                clearing_price = (bid['price'] + ask['price']) / 2
                
                match = TradeMatch(
                    buyer_id=bid['id'],
                    seller_id=ask['id'],
                    amount_kwh=amount,
                    price_per_kwh=clearing_price,
                    total_cost=network_cost_obj.total_cost, # Note: this uses base price in service, might need adjustment
                    score=result.fval # Optimization value
                )
                matches.append(match)

        duration = time.time() - start_time
        meta = {
            "duration": duration,
            "method": "VQE" if self.use_quantum else "Classical",
            "participants": len(sorted_bids) + len(sorted_asks),
            "variable_count": qp.get_num_binary_vars()
        }
        
        logger.info(f"Optimization finished in {duration:.3f}s. Matches: {len(matches)}")
        return matches, meta
