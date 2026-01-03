from typing import Dict, Tuple, List, Set
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..utils.transpilation_utils import (
    build_coupling_set,
    build_calibration_maps,
    calculate_circuit_metrics,
    track_single_qubit_gate,
    track_two_qubit_gate,
    estimate_swap_error,
    get_gate_duration,
    is_connected
)

def sabre_transpiler(
    qc: QuantumCircuit,
    topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:
    """
    Simple SABRE transpiler - pick SWAP that minimizes distances for front layer.
    """
    print(f"[SABRE] Starting SABRE transpilation")
    print(f"[SABRE] Circuit: {qc.num_qubits} qubits, {len(qc.operations)} operations")
    
    embedding = {i: i for i in range(qc.num_qubits)}
    coupling_set = build_coupling_set(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)
    distance_matrix = build_distance_matrix(qc.num_qubits, coupling_set)
    
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    gates_inserted = 0
    total_gate_error = 0.0
    total_duration = 0.0
    
    operations = list(qc.operations)
    executed = [False] * len(operations)
    dag_dependencies = build_dag_dependencies(operations)
    
    iteration = 0
    while not all(executed):
        iteration += 1
        if iteration > 10000:
            print(f"[SABRE] WARNING: Too many iterations, breaking")
            break
        
        front_layer = get_front_layer(operations, executed, dag_dependencies)
        
        if not front_layer:
            break
        
        executed_any = False
        for gate_idx in list(front_layer):
            op = operations[gate_idx]
            
            if not isinstance(op, Operation):
                transpiled_qc.operations.append(op)
                executed[gate_idx] = True
                executed_any = True
                continue
            
            # Single-qubit gates
            if len(op.qubits) == 1:
                transpiled_qc.operations.append(op)
                executed[gate_idx] = True
                executed_any = True
                error, duration = track_single_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration
            
            # Two-qubit gates
            elif len(op.qubits) == 2:
                q0, q1 = op.qubits
                p0, p1 = embedding[q0], embedding[q1]
                
                if is_connected(p0, p1, coupling_set):
                    transpiled_qc.operations.append(op)
                    executed[gate_idx] = True
                    executed_any = True
                    error, duration = track_two_qubit_gate(
                        op, embedding, gate_error_map, gate_duration_map
                    )
                    total_gate_error += error
                    total_duration += duration
            
            elif len(op.qubits) > 2:
                raise NotImplementedError(
                    f"Multi-qubit gate '{op.name}' with {len(op.qubits)} qubits is not supported."
                )
        
        # If no gate executed, insert SWAP
        if not executed_any:
            best_swap = find_best_swap_simple(
                front_layer, operations, embedding, coupling_set, distance_matrix
            )
            
            if best_swap:
                q0, q1 = best_swap
                swap_op = Operation(name="swap", qubits=[q0, q1])
                transpiled_qc.operations.append(swap_op)
                gates_inserted += 1
                
                if gates_inserted % 50 == 0 or gates_inserted <= 10:
                    print(f"[SABRE] Inserted SWAP #{gates_inserted}: logical ({q0},{q1})")
                
                p0, p1 = embedding[q0], embedding[q1]
                swap_error = estimate_swap_error(p0, p1, gate_error_map)
                cx_duration = get_gate_duration("cx", [p0, p1], gate_duration_map)
                total_gate_error += swap_error
                total_duration += 3 * cx_duration
                
                embedding[q0], embedding[q1] = embedding[q1], embedding[q0]
            else:
                print(f"[SABRE] ERROR: No valid SWAP found but gates still blocked!")
                break
    
    print(f"[SABRE] Transpilation complete: {gates_inserted} SWAPs inserted")
    
    transpiled_qc.depth = transpiled_qc.calculate_depth()
    
    metrics = calculate_circuit_metrics(
        original_qc=qc,
        transpiled_qc=transpiled_qc,
        gates_inserted=gates_inserted,
        total_gate_error=total_gate_error,
        total_duration=total_duration,
        embedding=embedding,
        topology=topology,
    )
    
    # Clean up metrics for JSON serialization
    for key, value in metrics.items():
        if isinstance(value, float):
            if value != value:  # NaN
                metrics[key] = 0.0
            elif value == float('inf') or value == float('-inf'):
                metrics[key] = 999999.0 if value > 0 else -999999.0
    
    return transpiled_qc, embedding, metrics


def build_distance_matrix(num_qubits: int, coupling_set: Set[Tuple[int, int]]) -> Dict[Tuple[int, int], int]:
    """Build shortest path distance matrix using Floyd-Warshall."""
    INF = 999999
    dist = {}
    
    for i in range(num_qubits):
        for j in range(num_qubits):
            if i == j:
                dist[(i, j)] = 0
            else:
                dist[(i, j)] = INF
    
    for (i, j) in coupling_set:
        dist[(i, j)] = 1
        dist[(j, i)] = 1
    
    # Floyd-Warshall
    for k in range(num_qubits):
        for i in range(num_qubits):
            for j in range(num_qubits):
                if dist[(i, k)] + dist[(k, j)] < dist[(i, j)]:
                    dist[(i, j)] = dist[(i, k)] + dist[(k, j)]
    
    return dist


def build_dag_dependencies(operations: List) -> Dict[int, Set[int]]:
    """Build DAG of gate dependencies based on qubit usage."""
    dependencies = {i: set() for i in range(len(operations))}
    last_gate_on_qubit = {}
    
    for idx, op in enumerate(operations):
        if isinstance(op, Operation):
            try:
                qubits = op.qubits
                for qubit in qubits:
                    if qubit in last_gate_on_qubit:
                        dependencies[idx].add(last_gate_on_qubit[qubit])
                    last_gate_on_qubit[qubit] = idx
            except (AttributeError, TypeError):
                pass
    
    return dependencies


def get_front_layer(operations: List, executed: List[bool], dependencies: Dict[int, Set[int]]) -> List[int]:
    """Get gates whose dependencies are all executed."""
    front = []
    for idx in range(len(operations)):
        if not executed[idx]:
            if all(executed[dep] for dep in dependencies[idx]):
                front.append(idx)
    return front


def find_best_swap_simple(
    front_layer: List[int],
    operations: List,
    embedding: Dict[int, int],
    coupling_set: Set[Tuple[int, int]],
    distance_matrix: Dict[Tuple[int, int], int]
) -> Tuple[int, int]:
    """
    Dead simple SABRE: find SWAP that minimizes total distance for front layer 2q gates.
    Only consider SWAPs that help BLOCKED gates.
    """
    # Get BLOCKED 2-qubit gates in front layer
    blocked_gates = []
    blocked_qubits = set()
    
    for idx in front_layer:
        op = operations[idx]
        if isinstance(op, Operation):
            try:
                if len(op.qubits) == 2:
                    q0, q1 = op.qubits
                    p0, p1 = embedding[q0], embedding[q1]
                    # Check if connected
                    if not is_connected(p0, p1, coupling_set):
                        blocked_gates.append((q0, q1))
                        blocked_qubits.add(q0)
                        blocked_qubits.add(q1)
            except (AttributeError, TypeError):
                pass
    
    if not blocked_qubits:
        # No blocked gates, shouldn't happen
        return None
    
    # Get candidate SWAPs: ONLY on edges touching BLOCKED qubits
    candidate_swaps = set()
    for q in blocked_qubits:
        p = embedding[q]
        for (p1, p2) in coupling_set:
            if p == p1:
                for lq, pq in embedding.items():
                    if pq == p2:
                        candidate_swaps.add(tuple(sorted([q, lq])))
            elif p == p2:
                for lq, pq in embedding.items():
                    if pq == p1:
                        candidate_swaps.add(tuple(sorted([q, lq])))
    
    if not candidate_swaps:
        return None
    
    # Pick SWAP that minimizes sum of distances for BLOCKED gates
    best_swap = None
    best_cost = float('inf')
    
    for swap in candidate_swaps:
        q0, q1 = swap
        temp_embedding = embedding.copy()
        temp_embedding[q0], temp_embedding[q1] = temp_embedding[q1], temp_embedding[q0]
        
        # Calculate total distance for BLOCKED gates after this SWAP
        total_dist = 0
        for g_q0, g_q1 in blocked_gates:
            p0 = temp_embedding[g_q0]
            p1 = temp_embedding[g_q1]
            dist = distance_matrix.get((p0, p1), 999999)
            total_dist += dist
        
        if total_dist < best_cost:
            best_cost = total_dist
            best_swap = swap
    
    return best_swap


def is_connected(p0: int, p1: int, coupling_set: Set[Tuple[int, int]]) -> bool:
    """Check if two physical qubits are connected."""
    return (p0, p1) in coupling_set or (p1, p0) in coupling_set