from typing import Dict, List, Tuple, Set
from ..core.QuantumCircuit import QuantumCircuit, Operation
import math

def build_coupling_set(coupling_map: List[List[int]]) -> Set[Tuple[int, int]]:
    coupling_set: Set[Tuple[int, int]] = set()
    for edge in coupling_map:
        coupling_set.add((edge[0], edge[1]))
        coupling_set.add((edge[1], edge[0]))
    return coupling_set


def build_calibration_maps(topology) -> Tuple[Dict, Dict]:
    gate_error_map = {}
    gate_duration_map = {}

    if topology.calibrationData:
        for gate_cal in topology.calibrationData.gates:
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


def calculate_circuit_metrics(
    original_qc: QuantumCircuit,
    transpiled_qc: QuantumCircuit,
    gates_inserted: int,
    total_gate_error: float,
    total_duration: float,
    embedding: Dict[int, int],
    topology,
) -> Dict[str, float]:
    """
    Metrics use FIRST-ORDER additive error model (physically consistent).
    """

    original_depth = original_qc.depth
    transpiled_depth = transpiled_qc.depth
    depth_increase = transpiled_depth - original_depth

    total_gates = len([
        op for op in transpiled_qc.operations
        if isinstance(op, Operation)
    ])

    n_swap_gates = sum(
        1 for op in transpiled_qc.operations
        if isinstance(op, Operation) and op.name.lower() == "swap"
    )

    # IMPORTANT: SWAP = 3 CX gates
    n_explicit_cx = sum(
        1 for op in transpiled_qc.operations
        if isinstance(op, Operation) and op.name.lower() == "cx"
    )
    n_cx_gates = n_explicit_cx + (3 * n_swap_gates)

    # === Error model: additive, conservative ===
    gate_error = min(total_gate_error, 1.0)

    # Readout error (mean over used physical qubits)
    readout_error = 0.0
    if topology.calibrationData:
        readout_errors = [
            q.readout_error
            for q in topology.calibrationData.qubits
            if q.qubit in embedding.values() and q.readout_error is not None
        ]
        if readout_errors:
            readout_error = sum(readout_errors) / len(readout_errors)

    total_error_rate = min(gate_error + readout_error, 1.0)
    fidelity = max(1.0 - total_error_rate, 0.0)

    decoherence_errors = []

    if topology.calibrationData:
        for qubit_cal in topology.calibrationData.qubits:
            if qubit_cal.qubit in embedding.values():
                t1 = qubit_cal.t1
                t2 = qubit_cal.t2
                if t1 and t2:
                    rate = (1.0 / t1) + (1.0 / t2)
                    decoh_error = 1 - math.exp(-total_duration * rate)
                    decoherence_errors.append(decoh_error)

    decoherence_risk = (
        sum(decoherence_errors) / len(decoherence_errors)
        if decoherence_errors else 0.0
    )

    measured_logical = get_measured_logical_qubits(original_qc)
    # Fallback: if no explicit measurements, assume all logical qubits are measured
    if not measured_logical:
        measured_logical = list(range(original_qc.num_qubits))
    measured_physical = [embedding[q] for q in measured_logical if q in embedding]

    readout_errors = []
    if topology.calibrationData:
        for qubit_cal in topology.calibrationData.qubits:
            if qubit_cal.qubit in measured_physical and qubit_cal.readout_error:
                readout_errors.append(qubit_cal.readout_error)

    readout_error = (
        sum(readout_errors) / len(readout_errors)
        if readout_errors else 0.0
    )

    def combine_errors(*errors: float) -> float:
        prob_no_error = 1.0
        for e in errors:
            prob_no_error *= (1.0 - e)
        return 1.0 - prob_no_error

    effective_error = combine_errors(total_gate_error, decoherence_risk, readout_error)
    fidelity = max(1.0 - effective_error, 0.0)

    print(n_cx_gates)
    return {
        "execution_time": total_duration,
        "gate_error": total_gate_error,
        "decoherence_risk": decoherence_risk,
        "readout_error": readout_error,
        "effective_error": effective_error,
        "fidelity": fidelity,
        "gates_inserted": float(gates_inserted),
        "depth_increase": float(depth_increase),
        "n_swap_gates": float(n_swap_gates),
        "n_cx_gates": float(n_cx_gates),
        "total_gates": float(total_gates),
        "original_depth": float(original_depth),
        "transpiled_depth": float(transpiled_depth),
    }



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


def estimate_swap_error(
    physical_q0: int,
    physical_q1: int,
    gate_error_map: Dict,
    default_cx_error: float = 0.01
) -> float:
    """
    SWAP = 3 CX gates (compounded).
    """
    cx_error = get_gate_error(
        "cx", [physical_q0, physical_q1], gate_error_map, default_cx_error
    )
    return 1 - (1 - cx_error) ** 3


def is_connected(
    qubit1: int,
    qubit2: int,
    coupling_set: Set[Tuple[int, int]]
) -> bool:
    return (qubit1, qubit2) in coupling_set

def get_measured_logical_qubits(qc: QuantumCircuit) -> List[int]:
    measured = set()
    for op in qc.operations:
        if isinstance(op, Operation) and op.name.lower() in {"measure", "measure_all"}:
            measured.update(op.qubits)
    return list(measured)
