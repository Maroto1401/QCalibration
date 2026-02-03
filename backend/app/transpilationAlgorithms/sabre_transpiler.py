import math
from typing import Dict, Tuple
import random
from collections import defaultdict, deque
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..core.BaseModelClasses import Topology
from ..utils.transpilation_utils import (
    build_calibration_maps,
    calculate_circuit_metrics,
    track_single_qubit_gate,
    track_two_qubit_gate,
)

# ======================= SABRE TRANSPILER (CORRECTED) =======================
PI = math.pi

def sabre_transpiler(
    qc: QuantumCircuit,
    topology: Topology,
    max_swaps_per_gate: int = 10
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:
    """
    SABRE transpiler with dynamic embedding and proper physical qubit tracking.
    
    Key difference from naive:
    - Uses a heuristic (distance-based) to choose which SWAPs to apply
    - Embedding evolves throughout transpilation
    - Gates are applied to CURRENT physical positions (after SWAPs)
    
    CRITICAL FIX: When applying two-qubit gates, use current embedding positions,
    not the original logical qubit indices.
    """

    print("[SABRE] Starting SABRE transpilation")

    coupling_set = build_coupling_set(topology.coupling_map)
    adjacency = _build_adjacency_list(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    # Dynamic embedding: evolves as we insert SWAPs
    embedding = {i: i for i in range(qc.num_qubits)}
    distance_matrix = _build_distance_matrix_fast(adjacency, topology.numQubits)

    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    # Metrics
    logical_swap_count = 0
    routing_gate_count = 0

    operations = list(qc.operations)
    dependencies = _build_dependencies(operations)
    executed = [False] * len(operations)
    swaps_per_gate = defaultdict(int)

    iteration = 0

    # ---------- SWAP DECOMPOSITION ----------
    def decompose_swap(swap_q0: int, swap_q1: int, embedding: Dict[int, int]):
        """Decompose a logical SWAP into physical CX gates"""
        p0, p1 = embedding[swap_q0], embedding[swap_q1]
        ops = []

        cx_pairs = [(p0, p1), (p1, p0), (p0, p1)]
        for control, target in cx_pairs:
            # H on target: SX RZ(π/2) SX
            ops.append(Operation("sx", qubits=[target]))
            ops.append(Operation("rz", qubits=[target], params=[PI/2]))
            ops.append(Operation("sx", qubits=[target]))

            # CZ
            ops.append(Operation("cz", qubits=[control, target]))

            # H on target: SX RZ(π/2) SX
            ops.append(Operation("sx", qubits=[target]))
            ops.append(Operation("rz", qubits=[target], params=[PI/2]))
            ops.append(Operation("sx", qubits=[target]))

        return ops, len(ops)

    # ================= MAIN LOOP =================
    while not all(executed):
        iteration += 1
        front_layer = _get_front_layer(executed, dependencies)

        if not front_layer:
            break

        progress = False

        # ----- Try to execute gates -----
        for idx in front_layer:
            if executed[idx]:
                continue

            op = operations[idx]

            if not isinstance(op, Operation):
                transpiled_qc.operations.append(op)
                executed[idx] = True
                progress = True
                continue

            # ---------- SINGLE-QUBIT GATES ----------
            if len(op.qubits) == 1:
                q0 = op.qubits[0]
                p0 = embedding[q0]  # Get CURRENT physical position

                # Create operation with current physical qubit
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata
                )
                transpiled_qc.operations.append(phys_op)
                
                error, duration = track_single_qubit_gate(
                    phys_op, embedding, gate_error_map, gate_duration_map
                )
                executed[idx] = True
                progress = True
                continue

            # ---------- TWO-QUBIT GATES ----------
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]  # Get CURRENT physical positions

            # Check if qubits are adjacent (in either direction)
            if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
                # Adjacent: apply gate at current physical positions
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0, p1],  # ← Use current physical positions!
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata
                )
                transpiled_qc.operations.append(phys_op)
                
                error, duration = track_two_qubit_gate(
                    phys_op, embedding, gate_error_map, gate_duration_map
                )
                executed[idx] = True
                progress = True
                continue

            # Not adjacent: needs SWAPs
            swaps_per_gate[idx] += 1
            if swaps_per_gate[idx] > max_swaps_per_gate:
                # Give up and apply gate anyway
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0, p1],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata
                )
                transpiled_qc.operations.append(phys_op)
                executed[idx] = True
                progress = True

        if progress:
            continue

        # ----- No progress: insert a SWAP -----
        blocked = []
        for idx in front_layer:
            op = operations[idx]
            if isinstance(op, Operation) and len(op.qubits) == 2:
                q0, q1 = op.qubits
                p0, p1 = embedding[q0], embedding[q1]
                if (p0, p1) not in coupling_set and (p1, p0) not in coupling_set:
                    d = distance_matrix.get((p0, p1), 999999)
                    blocked.append((idx, q0, q1, d))

        if not blocked:
            break

        # Find best SWAP using heuristic
        blocked.sort(key=lambda x: x[3], reverse=True)
        _, q0, q1, _ = blocked[0]

        best_swap = _find_swap_for_gate(q0, q1, embedding, adjacency, distance_matrix, coupling_set)
        if best_swap is None:
            best_swap = _find_random_swap_safe(embedding, adjacency)

        if best_swap is None:
            print("[SABRE] Could not find valid SWAP")
            break

        swap_q0, swap_q1 = best_swap

        print(f"[SABRE] Iteration {iteration}: Inserting SWAP({swap_q0}, {swap_q1}) "
              f"at physical ({embedding[swap_q0]}, {embedding[swap_q1]})")

        # ---- METRICS ----
        logical_swap_count += 1

        # ---- DECOMPOSE AND INSERT SWAP ----
        hw_ops, n_hw = decompose_swap(swap_q0, swap_q1, embedding)
        for hw_op in hw_ops:
            transpiled_qc.operations.append(hw_op)

        routing_gate_count += n_hw

        # ---- UPDATE EMBEDDING (CRITICAL) ----
        # This is a dynamic embedding: the mapping changes as we insert SWAPs
        embedding[swap_q0], embedding[swap_q1] = embedding[swap_q1], embedding[swap_q0]

    # ================= FINALIZE =================
    # Add any remaining unexecuted operations
    for i, done in enumerate(executed):
        if not done:
            transpiled_qc.operations.append(operations[i])

    transpiled_qc.depth = transpiled_qc.calculate_depth()

    # Calculate metrics
    metrics = calculate_circuit_metrics(
        original_qc=qc,
        transpiled_qc=transpiled_qc,
        logical_swap_count=logical_swap_count,
        embedding=embedding,
        topology=topology,
    )

    metrics.update({
        "routing_gate_count": routing_gate_count,
        "total_physical_gates": len(transpiled_qc.operations),
        "iterations": iteration,
    })

    print(f"[SABRE] Transpilation finished")
    print(f"[SABRE] Final embedding: {embedding}")
    print(f"[SABRE] Logical SWAPs: {logical_swap_count}")
    print(f"[SABRE] Routing gates added: {routing_gate_count}")
    print(f"[SABRE] Total transpiled operations: {len(transpiled_qc.operations)}")
    print(f"[SABRE] Iterations: {iteration}")

    return transpiled_qc, embedding, metrics


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_coupling_set(coupling_map):
    """Build set of valid (control, target) pairs from coupling map"""
    # Convert lists to tuples if necessary (lists aren't hashable)
    return set(tuple(pair) if isinstance(pair, list) else pair for pair in coupling_map)

def _build_adjacency_list(coupling_map):
    """Build undirected adjacency list from coupling map"""
    adj = defaultdict(set)
    for u, v in coupling_map:
        adj[u].add(v)
        adj[v].add(u)
    return adj

def _build_distance_matrix_fast(adjacency, num_qubits):
    """Build all-pairs shortest path distances using BFS"""
    dist = {}
    for source in range(num_qubits):
        distances = {source: 0}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            current_dist = distances[current]
            for neighbor in adjacency.get(current, []):
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)
        for target, distance in distances.items():
            dist[(source, target)] = distance
    return dist

def _build_dependencies(operations):
    """Build dependency graph: which operations must execute before each operation"""
    num_ops = len(operations)
    dependencies = [set() for _ in range(num_ops)]
    last_gate_on_qubit = {}
    
    for idx, op in enumerate(operations):
        if isinstance(op, Operation) and hasattr(op, 'qubits'):
            for q in op.qubits:
                if q in last_gate_on_qubit:
                    dependencies[idx].add(last_gate_on_qubit[q])
                last_gate_on_qubit[q] = idx
    
    return dependencies

def _get_front_layer(executed, dependencies):
    """Get all ready-to-execute operations (front layer)"""
    front_layer = []
    for i in range(len(executed)):
        if not executed[i] and all(executed[dep] for dep in dependencies[i]):
            front_layer.append(i)
    return front_layer

def _find_swap_for_gate(q0: int, q1: int, embedding: Dict[int, int], 
                        adjacency: dict, distance_matrix: dict, 
                        coupling_set: set) -> Tuple[int, int]:
    """
    Find best SWAP using distance heuristic.
    
    Strategy:
    - Try swapping q0 with neighbors of p0
    - Try swapping q1 with neighbors of p1
    - Choose swap that gives best distance improvement
    """
    p0, p1 = embedding[q0], embedding[q1]
    current_dist = distance_matrix.get((p0, p1), 999999)
    
    if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
        return None
    
    best_swap = None
    best_improvement = -1
    
    # Try swapping q0 with neighbors of p0
    for neighbor_p in adjacency.get(p0, []):
        for l, p in embedding.items():
            if p == neighbor_p and l != q0:
                # Simulate swap
                temp_embedding = embedding.copy()
                temp_embedding[q0], temp_embedding[l] = temp_embedding[l], temp_embedding[q0]
                new_p0 = temp_embedding[q0]
                new_dist = distance_matrix.get((new_p0, p1), 999999)
                improvement = current_dist - new_dist
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = tuple(sorted([q0, l]))
    
    # Try swapping q1 with neighbors of p1
    for neighbor_p in adjacency.get(p1, []):
        for l, p in embedding.items():
            if p == neighbor_p and l != q1:
                # Simulate swap
                temp_embedding = embedding.copy()
                temp_embedding[q1], temp_embedding[l] = temp_embedding[l], temp_embedding[q1]
                new_p1 = temp_embedding[q1]
                new_dist = distance_matrix.get((p0, new_p1), 999999)
                improvement = current_dist - new_dist
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = tuple(sorted([q1, l]))
    
    if best_improvement > 0:
        return best_swap
    
    return None

def _find_random_swap_safe(embedding: Dict[int, int], adjacency: dict):
    """Find a random valid SWAP between adjacent physical qubits"""
    physical_to_logical = {p: l for l, p in embedding.items()}
    possible_swaps = []
    
    for p0 in physical_to_logical.keys():
        for p1 in adjacency.get(p0, []):
            if p1 in physical_to_logical:
                l0 = physical_to_logical[p0]
                l1 = physical_to_logical[p1]
                if l0 != l1:
                    possible_swaps.append(tuple(sorted([l0, l1])))
    
    if possible_swaps:
        return random.choice(possible_swaps)
    
    return None