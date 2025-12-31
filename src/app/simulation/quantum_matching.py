
import logging
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Qiskit Imports
from qiskit_algorithms import NumPyMinimumEigensolver, QAOA
from qiskit_algorithms.optimizers import SLSQP
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as Sampler

logger = logging.getLogger(__name__)

@dataclass
class TradeMatch:
    buyer_id: str
    seller_id: str
    amount_kwh: float
    price_per_kwh: float
    total_cost: float
    score: float

class TranspiledQAOA(QAOA):
    """
    Custom QAOA that enforces transpilation of the dynamically generated ansatz
    to ensure compatibility with AerSimulator and SamplerV2.
    """
    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = backend
        self._pm = generate_preset_pass_manager(backend=self.backend, optimization_level=1)

    def _check_operator_ansatz(self, operator):
        # Let the parent create the QAOAAnsatz
        super()._check_operator_ansatz(operator)
        # Transpile it to decompose high-level gates (QAOA, PauliEvolution)
        if self.ansatz is not None:
            # logger.debug(f"Transpiling QAOA ansatz for backend {self.backend.name}")
            self.ansatz = self._pm.run(self.ansatz)

class QuantumMatching:
    """
    Quantum-Enhanced Optimizer for P2P Energy Trading.
    Uses VQE with a classical fallback to solve energy matching for social welfare.
    """

    def __init__(self, use_quantum: bool = True):
        self.use_quantum = use_quantum
        
        # Fallback classical solver always available
        self.classical_optimizer = NumPyMinimumEigensolver()
        self.classical_meo = MinimumEigenOptimizer(self.classical_optimizer)

        if self.use_quantum:
            try:
                # 1. Setup Backend & SamplerV2
                self.backend = AerSimulator()
                self.sampler = Sampler() # V2 does not take shots in init (uses default or run arg)
                
                # 2. Setup Optimizer
                self.optimizer = SLSQP(maxiter=20)
                
                # 3. Use TranspiledQAOA to handle circuit decomposition
                self.qaoa = TranspiledQAOA(
                    backend=self.backend,
                    sampler=self.sampler, 
                    optimizer=self.optimizer,
                    reps=1
                )
                self.meo = MinimumEigenOptimizer(self.qaoa)
                logger.info("QuantumMatching initialized with TranspiledQAOA + SamplerV2 (AerSimulator)")
            except Exception as e:
                logger.error(f"Failed to initialize Quantum QAOA: {e}. Falling back to Classical Mode.")
                self.use_quantum = False

    def optimize_matches(
        self, 
        bids: List[Dict], 
        asks: List[Dict], 
        cost_callback,
        zone_voltages: Optional[Dict[int, float]] = None
    ) -> Tuple[List[TradeMatch], Dict[str, Any]]:
        start_time = time.time()
        
        # 1. Candidate Selection (Top N to keep problem small for VQE/Simulators)
        # Problem: Match Bids to Asks to Maximize (Bid_p - Ask_p)*Amt - Friction + StabilityBonus
        sorted_bids = sorted(bids, key=lambda x: x['price'], reverse=True)[:3]
        sorted_asks = sorted(asks, key=lambda x: x['price'])[:3]
        
        if not sorted_bids or not sorted_asks:
            return [], {"status": "no_participants", "duration": time.time()-start_time}

        # 2. Construct Quadratic Program
        qp = QuadraticProgram("P2PMatching")
        vars_map = {}
        
        # Binary variables: x_ij = 1 if bid i is matched with ask j
        for i, bid in enumerate(sorted_bids):
            for j, ask in enumerate(sorted_asks):
                var_name = f"x_{i}_{j}"
                qp.binary_var(var_name)
                vars_map[var_name] = (i, j)

        # Objective Function: Maximize Social Welfare
        linear_terms = {}
        for var_name, (i, j) in vars_map.items():
            bid = sorted_bids[i]
            ask = sorted_asks[j]
            amount = min(bid['amount'], ask['amount'])
            
            # Get friction (Wheeling + Loss) from callback
            network_cost_obj = cost_callback(bid['zone'], ask['zone'], amount)
            friction = network_cost_obj.wheeling_charge + network_cost_obj.loss_cost
            
            # Grid Stability Bonus (based on local voltages)
            stability_bonus = 0.0
            if zone_voltages:
                v_buyer = zone_voltages.get(bid['zone'], 1.0)
                v_seller = zone_voltages.get(ask['zone'], 1.0)
                COEFF_STABILITY = 0.5
                
                if v_seller < 0.96: stability_bonus += COEFF_STABILITY
                elif v_seller > 1.04: stability_bonus -= COEFF_STABILITY
                if v_buyer > 1.04: stability_bonus += COEFF_STABILITY
                elif v_buyer < 0.96: stability_bonus -= COEFF_STABILITY
            
            # Social Welfare calculation
            energy_spread = (bid['price'] - ask['price']) * amount
            welfare = energy_spread - friction + stability_bonus
            
            logger.debug(f"TRACE {bid['id']}@{bid['price']:.2f} <-> {ask['id']}@{ask['price']:.2f} | "
                         f"Amt: {amount:.3f} | Spr: {energy_spread:.3f} | Fric: {friction:.3f} | "
                         f"Stab: {stability_bonus:.2f} => Welfare: {welfare:.3f}")
            
            # Minimize (-Welfare)
            linear_terms[var_name] = -welfare
            
        qp.minimize(linear=linear_terms)

        # Constraints: 1 bid per ask max, 1 ask per bid max
        for i in range(len(sorted_bids)):
            qp.linear_constraint(linear={f"x_{i}_{j}": 1 for j in range(len(sorted_asks))}, sense="<=", rhs=1)
        for j in range(len(sorted_asks)):
            qp.linear_constraint(linear={f"x_{k}_{j}": 1 for k in range(len(sorted_bids))}, sense="<=", rhs=1)

        # 3. Solve
        try:
            if self.use_quantum:
                result = self.meo.solve(qp)
            else:
                result = self.classical_meo.solve(qp)
        except Exception as e:
            logger.error(f"Optimization failed: {e}. Trying classical fallback...")
            result = self.classical_meo.solve(qp)
            self.use_quantum = False

        # 4. Parse Results
        matches = []
        if result.x is not None:
             for var_name, val in result.variables_dict.items():
                if val > 0.9:
                    i, j = vars_map[var_name]
                    bid, ask = sorted_bids[i], sorted_asks[j]
                    amount = min(bid['amount'], ask['amount'])
                    
                    net_cost = cost_callback(bid['zone'], ask['zone'], amount)
                    clearing_price = (bid['price'] + ask['price']) / 2
                    
                    matches.append(TradeMatch(
                        buyer_id=bid['id'],
                        seller_id=ask['id'],
                        amount_kwh=amount,
                        price_per_kwh=clearing_price,
                        total_cost=net_cost.total_cost,
                        score=-result.fval
                    ))

        if matches:
            logger.info(f"Quantum Optimization cleared {len(matches)} matches. Total Welfare: {-result.fval:.2f} THB")
        else:
            logger.info(f"Quantum Optimization returned 0 matches. Welfare: {-result.fval:.2f}")

        duration = time.time() - start_time
        return matches, {
            "duration": duration,
            "method": "QAOA" if self.use_quantum else "Classical",
            "participants": len(sorted_bids) + len(sorted_asks),
            "social_welfare": -result.fval,
            "status": result.status.name
        }
