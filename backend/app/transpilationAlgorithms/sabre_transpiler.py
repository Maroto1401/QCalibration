from typing import Dict, Tuple, List, Set
import random
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

# ---------------- SABRE TRANSPILER ----------------
def sabre_transpiler(
    qc: QuantumCircuit,
    topology,
    use_trivial_embedding: bool = False
) -> Tuple[QuantumCircuit, Dict[int,int], Dict[str,float]]:
    """
    SABRE transpiler with smart initial embedding.
    """
    print(f"[SABRE] Starting SABRE transpilation")
    print(f"[SABRE] Circuit: {qc.num_qubits} qubits, {len(qc.operations)} operations")
    print(f"[SABRE] Topology: {topology.numQubits} physical qubits available")

    coupling_set = build_coupling_set(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    # --- INITIAL EMBEDDING ---
    if use_trivial_embedding:
        print("[SABRE] Using trivial embedding (first n qubits)")
        embedding = {i:i for i in range(qc.num_qubits)}
    else:
        embedding = smart_initial_embedding(qc, topology, coupling_set, gate_error_map)
    print(f"[SABRE] Initial embedding: {embedding}")

    distance_matrix = build_distance_matrix(topology.numQubits, coupling_set)
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    operations = list(qc.operations)
    executed = [False]*len(operations)
    dag_dependencies = build_dag_dependencies(operations)

    gates_inserted = 0
    total_gate_error = 0.0
    total_duration = 0.0
    consecutive_swaps = 0
    gates_executed_count = 0

    max_iterations = 10000
    iteration = 0

    while not all(executed) and iteration < max_iterations:
        iteration += 1
        front_layer = get_front_layer(operations, executed, dag_dependencies)
        if not front_layer:
            break

        executed_any = False

        for idx in front_layer:
            op = operations[idx]
            if not isinstance(op, Operation) or not hasattr(op, 'qubits'):
                transpiled_qc.operations.append(op)
                executed[idx] = True
                executed_any = True
                consecutive_swaps = 0
                gates_executed_count += 1
                continue

            # Single-qubit gate
            if len(op.qubits) == 1:
                transpiled_qc.operations.append(op)
                executed[idx] = True
                executed_any = True
                consecutive_swaps = 0
                gates_executed_count += 1
                error, duration = track_single_qubit_gate(op, embedding, gate_error_map, gate_duration_map)
                total_gate_error += error
                total_duration += duration

            # Two-qubit gate
            elif len(op.qubits) == 2:
                q0,q1 = op.qubits
                p0,p1 = embedding[q0], embedding[q1]
                if is_connected(p0,p1,coupling_set):
                    transpiled_qc.operations.append(op)
                    executed[idx] = True
                    executed_any = True
                    consecutive_swaps = 0
                    gates_executed_count += 1
                    error, duration = track_two_qubit_gate(op, embedding, gate_error_map, gate_duration_map)
                    total_gate_error += error
                    total_duration += duration
            else:
                raise NotImplementedError(f"Multi-qubit gate {op.name} not supported")

        # If no gate executed, insert SWAP
        if not executed_any:
            consecutive_swaps += 1
            best_swap = find_best_swap(front_layer, operations, embedding, coupling_set, distance_matrix)
            if not best_swap:
                print("[SABRE] ERROR: No valid SWAP found, blocked gates remain")
                break

            q0,q1 = best_swap
            swap_op = Operation(name="swap", qubits=[q0,q1])
            transpiled_qc.operations.append(swap_op)
            gates_inserted += 1

            p0,p1 = embedding[q0], embedding[q1]
            swap_error = estimate_swap_error(p0,p1,gate_error_map)
            cx_duration = get_gate_duration("cx",[p0,p1],gate_duration_map)
            total_gate_error += swap_error
            total_duration += 3*cx_duration

            # Update embedding
            embedding[q0], embedding[q1] = embedding[q1], embedding[q0]

    # ---------------- FINALIZATION ----------------
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

    # Clean metrics for JSON
    for k,v in metrics.items():
        if isinstance(v,float):
            if v!=v: metrics[k]=0.0
            elif v==float('inf') or v==float('-inf'): metrics[k]=999999.0 if v>0 else -999999.0

    return transpiled_qc, embedding, metrics


# ---------------- HELPERS ----------------
def smart_initial_embedding(qc: QuantumCircuit, topology, coupling_set: Set[Tuple[int,int]], gate_error_map: Dict[Tuple[int,int], float]) -> Dict[int,int]:
    """
    Greedy embedding: place early interacting qubits physically close with low-error edges.
    """
    num_logical = qc.num_qubits
    num_physical = topology.numQubits
    if num_logical > num_physical:
        raise ValueError("Circuit requires more qubits than available")

    # Compute qubit quality
    qubit_quality = {}
    for p in range(num_physical):
        errors = [gate_error_map.get((p0,p1),1.0) for (p0,p1) in gate_error_map if p0==p or p1==p]
        qubit_quality[p] = sum(errors)/len(errors) if errors else 1.0

    embedding = {}
    used_physical = set()

    # Place qubits as they appear in the circuit
    for op in qc.operations:
        if not isinstance(op, Operation) or not hasattr(op,'qubits'):
            continue
        for q in op.qubits:
            if q in embedding: continue

            # Candidates connected to already placed qubits
            candidates = set()
            for placed_q, placed_p in embedding.items():
                for (p0,p1) in coupling_set:
                    if p0==placed_p and p1 not in used_physical: candidates.add(p1)
                    if p1==placed_p and p0 not in used_physical: candidates.add(p0)

            if candidates:
                best_p = min(candidates, key=lambda p: qubit_quality[p])
            else:
                available = [p for p in range(num_physical) if p not in used_physical]
                best_p = min(available, key=lambda p: qubit_quality[p])

            embedding[q] = best_p
            used_physical.add(best_p)

    # Fill remaining qubits
    for q in range(num_logical):
        if q not in embedding:
            for p in range(num_physical):
                if p not in used_physical:
                    embedding[q]=p
                    used_physical.add(p)
                    break

    return embedding


def build_distance_matrix(num_qubits: int, coupling_set: Set[Tuple[int,int]]) -> Dict[Tuple[int,int], int]:
    """Floyd-Warshall distance between physical qubits"""
    INF=999999
    dist = {(i,j):0 if i==j else INF for i in range(num_qubits) for j in range(num_qubits)}
    for (i,j) in coupling_set:
        dist[(i,j)] = 1
        dist[(j,i)] = 1
    for k in range(num_qubits):
        for i in range(num_qubits):
            for j in range(num_qubits):
                if dist[(i,k)] + dist[(k,j)] < dist[(i,j)]:
                    dist[(i,j)] = dist[(i,k)] + dist[(k,j)]
    return dist


def build_dag_dependencies(operations: List) -> Dict[int, Set[int]]:
    """DAG: track last gate on each qubit"""
    dependencies = {i:set() for i in range(len(operations))}
    last_gate = {}
    for idx, op in enumerate(operations):
        if isinstance(op, Operation) and hasattr(op,'qubits'):
            for q in op.qubits:
                if q in last_gate:
                    dependencies[idx].add(last_gate[q])
                last_gate[q] = idx
    return dependencies


def get_front_layer(operations: List, executed: List[bool], dependencies: Dict[int, Set[int]]) -> List[int]:
    """Gates ready to execute"""
    return [i for i in range(len(operations)) if not executed[i] and all(executed[dep] for dep in dependencies[i])]


def find_best_swap(front_layer: List[int], operations: List, embedding: Dict[int,int], coupling_set: Set[Tuple[int,int]], distance_matrix: Dict[Tuple[int,int], int]) -> Tuple[int,int]:
    """Pick SWAP that minimizes total distance of blocked 2q gates"""
    blocked_gates = []
    blocked_qubits = set()
    for idx in front_layer:
        op = operations[idx]
        if isinstance(op, Operation) and hasattr(op,'qubits') and len(op.qubits)==2:
            q0,q1 = op.qubits
            p0,p1 = embedding[q0], embedding[q1]
            if not is_connected(p0,p1,coupling_set):
                blocked_gates.append((q0,q1))
                blocked_qubits.update([q0,q1])

    if not blocked_qubits:
        return None

    # Candidate SWAPs: any pair touching blocked qubits
    candidate_swaps = set()
    for q in blocked_qubits:
        p = embedding[q]
        for (p0,p1) in coupling_set:
            if p==p0 or p==p1:
                for lq,l_p in embedding.items():
                    if l_p==p1 or l_p==p0:
                        candidate_swaps.add(tuple(sorted([q,lq])))

    if not candidate_swaps:
        return None

    # Pick SWAP minimizing sum of distances
    best_swap=None
    best_cost=float('inf')
    for q0,q1 in candidate_swaps:
        temp_emb = embedding.copy()
        temp_emb[q0],temp_emb[q1]=temp_emb[q1],temp_emb[q0]
        cost=sum(distance_matrix.get((temp_emb[g0],temp_emb[g1]),999999) for g0,g1 in blocked_gates)
        if cost<best_cost:
            best_cost=cost
            best_swap=(q0,q1)
    return best_swap
