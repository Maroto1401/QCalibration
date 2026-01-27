from typing import Dict, List, Tuple, Set, Optional
from ..core.QuantumCircuit import QuantumCircuit, Operation
import math

def build_coupling_set(coupling_map: List[List[int]]) -> Set[Tuple[int, int]]:
    """
    Builds a set of valid edges for O(1) lookups.
    """
    coupling_set: Set[Tuple[int, int]] = set()
    for edge in coupling_map:
        coupling_set.add((edge[0], edge[1]))
        coupling_set.add((edge[1], edge[0]))
    return coupling_set


def build_calibration_maps(topology) -> Tuple[Dict, Dict]:
    """
    Extracts gate properties from backend calibration data.
    """
    gate_error_map = {}
    gate_duration_map = {}

    if topology.calibrationData:
        for gate_cal in topology.calibrationData.gates:
            # Create a standardized key: (gate_name, sorted_qubits)
            key = (gate_cal.name.lower(), tuple(sorted(gate_cal.qubits)))
            
            if gate_cal.gate_error is not None:
                gate_error_map[key] = gate_cal.gate_error
            if gate_cal.duration is not None:
                gate_duration_map[key] = gate_cal.duration

    return gate_error_map, gate_duration_map


def get_gate_error(
    gate_name: str,
    qubits: List[int],
    gate_error_map: Dict,
    default_error: float = 0.001
) -> float:
    key = (gate_name.lower(), tuple(sorted(qubits)))
    return gate_error_map.get(key, default_error)


def get_gate_duration(
    gate_name: str,
    qubits: List[int],
    gate_duration_map: Dict,
    default_duration: float = 0.0
) -> float:
    key = (gate_name.lower(), tuple(sorted(qubits)))
    return gate_duration_map.get(key, default_duration)
def estimate_swap_error(
    physical_q0: int,
    physical_q1: int,
    gate_error_map: Dict,
    default_cx_error: float = 0.01
) -> float:
    """
    Estimates SWAP error assuming a decomposition into 3 CX gates.
    
    Logic:
    1. Retrieve the native CX error for the specific qubit pair.
    2. Calculate success probability for 3 sequential CXs.
    3. Return the complement (failure probability).
    
    Approximation: For small errors, this is roughly 3 * cx_error.
    """
    # 1. Get the native CX error for this edge
    cx_error = get_gate_error(
        "cx", 
        [physical_q0, physical_q1], 
        gate_error_map, 
        default_error=default_cx_error
    )

    # 2. Calculate compounded success probability 
    # (1 - error) * (1 - error) * (1 - error)
    swap_success_prob = (1.0 - cx_error) ** 3

    # 3. Return total error
    return 1.0 - swap_success_prob

def calculate_circuit_metrics(
    original_qc: QuantumCircuit,
    transpiled_qc: QuantumCircuit,
    logical_swap_count: int,
    total_gate_error: float,
    total_duration: float,
    embedding: Dict[int, int],
    topology,
) -> Dict[str, float]:
    """
    Calculates execution metrics preserving the frontend API contract.
    
    internal math:
    - 'Risk' keys use AVERAGES (useful for UI gauges).
    - 'Fidelity' uses JOINT PROBABILITY (useful for actual success prediction).
    """

    # --- 1. Structural Metrics ---
    original_depth = original_qc.depth
    transpiled_depth = transpiled_qc.depth
    depth_increase = transpiled_depth - original_depth

    # Count explicit operations
    total_gates = 0

    # --- 2. Error Metrics (The Math Part) ---

    # A. Gate Fidelity
    # We assume 'total_gate_error' passed in is the sum of errors (Taylor expansion approximation).
    # Probability of NO gate error:
    gate_fidelity = max(1.0 - total_gate_error, 0.0)

    # B. Readout Metrics
    measured_logical = get_measured_logical_qubits(original_qc)
    if not measured_logical:
        # If no explicit measure, assume we measure all logical qubits mapped
        measured_logical = list(original_qc.qubits) if hasattr(original_qc, 'qubits') else []

    readout_errors = []
    
    if topology.calibrationData:
        for logical_q in measured_logical:
            if logical_q in embedding:
                phys_q = embedding[logical_q]
                # Find calibration for this physical qubit
                q_cal = next((q for q in topology.calibrationData.qubits if q.qubit == phys_q), None)
                if q_cal and q_cal.readout_error is not None:
                    readout_errors.append(q_cal.readout_error)

    # UI Metric: Average Readout Error (easy to read)
    avg_readout_error = sum(readout_errors) / len(readout_errors) if readout_errors else 0.0
    
    # Internal Metric: Probability all readouts succeed
    # P_readout_success = (1-e1) * (1-e2) * ...
    readout_fidelity = 1.0
    for err in readout_errors:
        readout_fidelity *= (1.0 - err)

    # C. Decoherence Metrics
    decoherence_errors_per_qubit = []
    decoherence_fidelity = 1.0

    if topology.calibrationData:
        # We look at ALL active physical qubits, not just measured ones
        active_physical_qubits = set(embedding.values())
        
        for qubit_cal in topology.calibrationData.qubits:
            if qubit_cal.qubit in active_physical_qubits:
                t1 = qubit_cal.t1
                t2 = qubit_cal.t2
                
                if t1 and t2 and t1 > 0 and t2 > 0:
                    rate = (1.0 / t1) + (1.0 / t2)
                    
                    # Probability that THIS qubit survives the whole duration
                    prob_survival = math.exp(-total_duration * rate)
                    prob_failure = 1.0 - prob_survival
                    
                    decoherence_errors_per_qubit.append(prob_failure)
                    decoherence_fidelity *= prob_survival

    # Average Decoherence Risk 
    avg_decoherence_risk = (
        sum(decoherence_errors_per_qubit) / len(decoherence_errors_per_qubit)
        if decoherence_errors_per_qubit else 0.0
    )

    # --- 3. Final Aggregation ---

    # Total Fidelity (ESP - Estimated Success Probability)
    # F = F_gate * F_readout * F_decoherence
    total_fidelity = gate_fidelity * readout_fidelity * decoherence_fidelity
    
    # Effective Error (The inverse of fidelity)
    effective_total_error = 1.0 - total_fidelity

    return {
        # Timing
        "execution_time": total_duration,
        
        # User-facing "Risk" indicators (Averages/Sums)
        "gate_error": total_gate_error,
        "decoherence_risk": avg_decoherence_risk,  # Average probability of decay per qubit
        "readout_error": avg_readout_error,        # Average probability of readout fail
        
        # The Real "Score" (Joint Probabilities)
        "effective_error": effective_total_error,
        "fidelity": total_fidelity,
        
        # Structure
        "depth_increase": float(depth_increase),
        "n_swap_gates": float(logical_swap_count),
        "total_gates": float(total_gates),
        "original_depth": float(original_depth),
        "transpiled_depth": float(transpiled_depth),
    }

# --- Helper Functions ---

def track_single_qubit_gate(
    op: Operation,
    embedding: Dict[int, int],
    gate_error_map: Dict,
    gate_duration_map: Dict
) -> Tuple[float, float]:
    physical_qubit = embedding[op.qubits[0]]
    error = get_gate_error(op.name, [physical_qubit], gate_error_map)
    duration = get_gate_duration(op.name, [physical_qubit], gate_duration_map)
    return error, duration


def track_two_qubit_gate(
    op: Operation,
    embedding: Dict[int, int],
    gate_error_map: Dict,
    gate_duration_map: Dict
) -> Tuple[float, float]:
    physical_q0 = embedding[op.qubits[0]]
    physical_q1 = embedding[op.qubits[1]]
    error = get_gate_error(op.name, [physical_q0, physical_q1], gate_error_map)
    duration = get_gate_duration(op.name, [physical_q0, physical_q1], gate_duration_map)
    return error, duration


def get_measured_logical_qubits(qc: QuantumCircuit) -> List[int]:
    """Identify which logical qubits are actually measured."""
    measured = set()
    for op in qc.operations:
        if isinstance(op, Operation) and op.name.lower() in {"measure", "measure_all"}:
            measured.update(op.qubits)
    return list(measured)