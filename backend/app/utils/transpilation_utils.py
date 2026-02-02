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


def calculate_per_qubit_metrics(
    transpiled_qc: QuantumCircuit,
    embedding: Dict[int, int],
    gate_error_map: Dict,
    gate_duration_map: Dict,
    topology
) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, Dict[str, float]]]:
    """
    Calculate per-qubit execution times and decoherence metrics.
    
    Uses the standard quantum physics model for decoherence:
    - T1: Energy relaxation (exponential decay with rate 1/T1)
    - T2: Dephasing time (exponential decay with rate 1/T2)
    - Combined: F_decoherence = exp(-t_exec / T1) * exp(-t_exec / T2)
              = exp(-t_exec * (1/T1 + 1/T2))
    
    This is the model used in IBM Qiskit, Cirq, and standard quantum computing frameworks.
    
    Returns:
        per_qubit_duration: Dict mapping physical_qubit -> total_execution_time
        per_qubit_decoherence_error: Dict mapping physical_qubit -> decoherence_error_probability
        per_qubit_t1_t2_errors: Dict mapping physical_qubit -> {'t1_error': float, 't2_error': float}
    """
    per_qubit_duration = {}
    per_qubit_decoherence_error = {}
    per_qubit_t1_t2_errors = {}
    
    # Initialize all active physical qubits
    active_physical_qubits = set(embedding.values())
    for phys_q in active_physical_qubits:
        per_qubit_duration[phys_q] = 0.0
        per_qubit_decoherence_error[phys_q] = 0.0
        per_qubit_t1_t2_errors[phys_q] = {'t1_error': 0.0, 't2_error': 0.0}
    
    # Accumulate execution time for each qubit based on gates
    if hasattr(transpiled_qc, 'operations'):
        for op in transpiled_qc.operations:
            # Skip measurements for duration accumulation (they're fast)
            if op.name.lower() in {"measure", "measure_all"}:
                continue
            
            # Get duration for this gate
            gate_duration = 0.0
            if len(op.qubits) == 1 and op.qubits[0] in embedding:
                phys_q = embedding[op.qubits[0]]
                gate_duration = get_gate_duration(op.name, [phys_q], gate_duration_map)
                per_qubit_duration[phys_q] += gate_duration
            
            elif len(op.qubits) == 2 and op.qubits[0] in embedding and op.qubits[1] in embedding:
                phys_q0 = embedding[op.qubits[0]]
                phys_q1 = embedding[op.qubits[1]]
                gate_duration = get_gate_duration(op.name, [phys_q0, phys_q1], gate_duration_map)
                per_qubit_duration[phys_q0] += gate_duration
                per_qubit_duration[phys_q1] += gate_duration
    
    # Calculate T1 and T2 decoherence errors for each qubit
    # Standard quantum physics model: combined decoherence = T1 * T2 effects
    if topology.calibrationData:
        for qubit_cal in topology.calibrationData.qubits:
            phys_q = qubit_cal.qubit
            if phys_q in active_physical_qubits:
                t1 = qubit_cal.t1
                t2 = qubit_cal.t2
                t_exec = per_qubit_duration.get(phys_q, 0.0)
                
                # Calculate individual T1 and T2 errors
                if t1 and t1 > 0:
                    # T1 error: probability of energy relaxation
                    # Fidelity from T1: F_T1 = exp(-t_exec / T1)
                    t1_fidelity = math.exp(-t_exec / t1)
                    t1_error = 1.0 - t1_fidelity
                    per_qubit_t1_t2_errors[phys_q]['t1_error'] = t1_error
                else:
                    t1_fidelity = 1.0
                
                if t2 and t2 > 0:
                    # T2 error: probability of dephasing
                    # Fidelity from T2: F_T2 = exp(-t_exec / T2)
                    t2_fidelity = math.exp(-t_exec / t2)
                    t2_error = 1.0 - t2_fidelity
                    per_qubit_t1_t2_errors[phys_q]['t2_error'] = t2_error
                else:
                    t2_fidelity = 1.0
                
                # Combined decoherence (standard physics model)
                # Fidelity_decoherence = exp(-t_exec / T1) * exp(-t_exec / T2)
                #                      = exp(-t_exec * (1/T1 + 1/T2))
                # This assumes T1 and T2 processes are independent
                if t1 and t2 and t1 > 0 and t2 > 0:
                    decoherence_fidelity = t1_fidelity * t2_fidelity
                    decoherence_error = 1.0 - decoherence_fidelity
                    per_qubit_decoherence_error[phys_q] = decoherence_error
                elif t1 and t1 > 0:
                    # Only T1 available
                    per_qubit_decoherence_error[phys_q] = t1_error
                elif t2 and t2 > 0:
                    # Only T2 available
                    per_qubit_decoherence_error[phys_q] = t2_error
    
    return per_qubit_duration, per_qubit_decoherence_error, per_qubit_t1_t2_errors

def calculate_circuit_metrics(
    original_qc: QuantumCircuit,
    transpiled_qc: QuantumCircuit,
    logical_swap_count: int,
    embedding: Dict[int, int],
    topology,
) -> Dict[str, float]:
    """
    Calculate comprehensive circuit metrics including per-qubit and overall fidelity.
    
    Returns a dictionary containing:
        - Structural metrics (depth, gate counts)
        - Gate error metrics (overall and per-operation)
        - Readout error metrics (per-qubit and overall)
        - Decoherence metrics (per-qubit T1/T2 errors and overall decoherence)
        - Execution time metrics (per-qubit and total)
        - Fidelity estimation (product of all error sources)
    """

    # Build calibration maps locally for accurate error/duration lookup
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    # --- 1. Structural Metrics ---
    original_depth = getattr(original_qc, 'depth', 0)
    transpiled_depth = getattr(transpiled_qc, 'depth', 0)
    depth_increase = transpiled_depth - original_depth
    
    total_gates = len(transpiled_qc.operations) if hasattr(transpiled_qc, 'operations') else 0

    # --- 2. Gate Error Metrics ---
    # Product of fidelities for actual gate error calculation
    gate_fidelity = 1.0
    gate_errors_list = []
    
    if hasattr(transpiled_qc, 'operations'):
        for op in transpiled_qc.operations:
            # Skip measurements for gate error (readout handled separately)
            if op.name.lower() in {"measure", "measure_all"}:
                continue
            
            current_error = 0.0
            
            if len(op.qubits) == 1 and op.qubits[0] in embedding:
                current_error, _ = track_single_qubit_gate(op, embedding, gate_error_map, gate_duration_map)
                gate_errors_list.append(current_error)
            
            elif len(op.qubits) == 2 and op.qubits[0] in embedding and op.qubits[1] in embedding:
                current_error, _ = track_two_qubit_gate(op, embedding, gate_error_map, gate_duration_map)
                gate_errors_list.append(current_error)
            
            # Multiply the success probability (P_success = 1 - P_fail)
            gate_fidelity *= (1.0 - current_error)

    # Overall gate error (for reference/UI: sum of individual errors)
    overall_gate_error = 1.0 - gate_fidelity if gate_fidelity < 1.0 else 0.0

    # --- 3. Per-Qubit Metrics ---
    per_qubit_duration, per_qubit_decoherence_error, per_qubit_t1_t2_errors = calculate_per_qubit_metrics(
        transpiled_qc, embedding, gate_error_map, gate_duration_map, topology
    )

    # --- 4. Readout Error Metrics ---
    # Get readout errors for all physical qubits in the embedding
    readout_errors = []
    readout_fidelity = 1.0
    
    if topology.calibrationData:
        for _, phys_q in embedding.items():
            q_cal = next((q for q in topology.calibrationData.qubits if q.qubit == phys_q), None)
            if q_cal and q_cal.readout_error is not None:
                readout_err = q_cal.readout_error
                readout_errors.append(readout_err)
                readout_fidelity *= (1.0 - readout_err)

    overall_readout_error = sum(readout_errors) if readout_errors else 0.0
    avg_readout_error = overall_readout_error / len(readout_errors) if readout_errors else 0.0

    # --- 5. Decoherence Metrics ---
    decoherence_fidelity = 1.0
    avg_decoherence_error = 0.0
    
    if per_qubit_decoherence_error:
        decoherence_errors = list(per_qubit_decoherence_error.values())
        for err in decoherence_errors:
            decoherence_fidelity *= (1.0 - err)
        avg_decoherence_error = sum(decoherence_errors) / len(decoherence_errors)

    # --- 6. Overall Execution Time ---
    overall_execution_time = max(per_qubit_duration.values()) if per_qubit_duration else 0.0

    # --- 7. Final Fidelity Calculation ---
    # Product of all fidelities: gate_fidelity * readout_fidelity * decoherence_fidelity
    total_fidelity = gate_fidelity * readout_fidelity * decoherence_fidelity
    effective_total_error = 1.0 - total_fidelity

    # --- 8. Build Per-Qubit Details Dictionary ---
    per_qubit_details = {}
    for phys_q in per_qubit_duration.keys():
        per_qubit_details[str(phys_q)] = {
            "execution_time": per_qubit_duration[phys_q],
            "t1_error": per_qubit_t1_t2_errors[phys_q]['t1_error'],
            "t2_error": per_qubit_t1_t2_errors[phys_q]['t2_error'],
            "decoherence_error": per_qubit_decoherence_error[phys_q],
        }

    # --- Return Metrics Dictionary ---
    return {
        # Structural metrics
        "original_depth": float(original_depth),
        "transpiled_depth": float(transpiled_depth),
        "depth_increase": float(depth_increase),
        "total_gates": float(total_gates),
        "n_swap_gates": float(logical_swap_count),
        
        # Gate error metrics
        "overall_gate_error": float(overall_gate_error),
        "gate_fidelity": float(gate_fidelity),
        
        # Readout error metrics
        "overall_readout_error": float(overall_readout_error),
        "avg_readout_error": float(avg_readout_error),
        "readout_fidelity": float(readout_fidelity),
        
        # Decoherence metrics
        "avg_decoherence_error": float(avg_decoherence_error),
        "decoherence_fidelity": float(decoherence_fidelity),
        
        # Execution time metrics
        "overall_execution_time": float(overall_execution_time),
        
        # Final fidelity
        "effective_error": float(effective_total_error),
        "fidelity": float(total_fidelity),
        
        # Per-qubit detailed metrics
        "per_qubit_metrics": per_qubit_details,
    }

# --- Helper Functions ---

def track_single_qubit_gate(
    op: Operation,
    embedding: Dict[int, int],
    gate_error_map: Dict,
    gate_duration_map: Dict
) -> Tuple[float, float]:
    """Get error and duration for a single-qubit gate."""
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
    """Get error and duration for a two-qubit gate."""
    physical_q0 = embedding[op.qubits[0]]
    physical_q1 = embedding[op.qubits[1]]
    error = get_gate_error(op.name, [physical_q0, physical_q1], gate_error_map)
    duration = get_gate_duration(op.name, [physical_q0, physical_q1], gate_duration_map)
    return error, duration


def get_measured_logical_qubits(qc: QuantumCircuit) -> List[int]:
    """Identify which logical qubits are actually measured."""
    measured = set()
    if hasattr(qc, 'operations'):
        for op in qc.operations:
            if isinstance(op, Operation) and op.name.lower() in {"measure", "measure_all"}:
                measured.update(op.qubits)
    return list(measured)