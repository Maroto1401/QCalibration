import math
from typing import Dict, Tuple
import random
from collections import defaultdict, deque
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..utils.transpilation_utils import (
    build_coupling_set,
    build_calibration_maps,
    calculate_circuit_metrics,
    track_single_qubit_gate,
    track_two_qubit_gate,
)

# ======================= SABRE TRANSPILER =======================

def sabre_transpiler(
    qc: QuantumCircuit,
    topology,
    max_swaps_per_gate: int = 10
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:

    print("SABRE: Starting transpilation")

    coupling_set = build_coupling_set(topology.coupling_map)
    adjacency = _build_adjacency_list(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    embedding = {i: i for i in range(qc.num_qubits)}
    distance_matrix = _build_distance_matrix_fast(adjacency, topology.numQubits)

    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    # ---------------- METRICS ----------------
    logical_swap_count = 0 # Logical SWAP gates inserted
    routing_gate_count = 0 # Physical gates added for routing
    total_gate_error = 0.0
    total_duration = 0.0

    operations = list(qc.operations)
    dependencies = _build_dependencies_debug(operations)
    executed = [False] * len(operations)
    swaps_per_gate = defaultdict(int)

    iteration = 0

    # ---------- SWAP DECOMPOSITION (CZ + SX + RZ) ----------
    def decompose_swap(op: Operation, embedding: Dict[int, int]):
        p0, p1 = embedding[op.qubits[0]], embedding[op.qubits[1]]
        ops = []

        cx_pairs = [(p0, p1), (p1, p0), (p0, p1)]
        for control, target in cx_pairs:
            # H on target
            ops.append(Operation("rz", qubits=[target], params=[math.pi]))
            ops.append(Operation("sx", qubits=[target]))
            ops.append(Operation("rz", qubits=[target], params=[math.pi]))

            # CZ
            ops.append(Operation("cz", qubits= [control, target]))

            # H on target
            ops.append(Operation("rz", qubits=[target], params=[math.pi]))
            ops.append(Operation("sx", qubits=[target]))
            ops.append(Operation("rz", qubits=[target], params=[math.pi]))

        return ops, len(ops)


    # ================= MAIN LOOP =================
    while not all(executed):
        iteration += 1
        front_layer = _get_front_layer_debug(executed, dependencies)

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

            # Single-qubit
            if len(op.qubits) == 1:
                transpiled_qc.operations.append(op)
                error, duration = track_single_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration
                executed[idx] = True
                progress = True
                continue

            # Two-qubit
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]

            if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
                transpiled_qc.operations.append(op)
                error, duration = track_two_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration
                executed[idx] = True
                progress = True
            else:
                swaps_per_gate[idx] += 1
                if swaps_per_gate[idx] > max_swaps_per_gate:
                    transpiled_qc.operations.append(op)
                    executed[idx] = True
                    progress = True

        if progress:
            continue

        # ----- Insert SWAP -----
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

        blocked.sort(key=lambda x: x[3], reverse=True)
        _, q0, q1, _ = blocked[0]

        best_swap = _find_swap_for_gate(q0, q1, embedding, adjacency, distance_matrix, coupling_set)
        if best_swap is None:
            best_swap = _find_random_swap_safe(embedding, adjacency)

        if best_swap is None:
            break

        swap_q0, swap_q1 = best_swap
        swap_op = Operation("swap", [swap_q0, swap_q1])

        # ---- LOGICAL SWAP METRICS ----
        logical_swap_count += 1

        # ---- PHYSICAL DECOMPOSITION ----
        hw_ops, n_hw = decompose_swap(swap_op, embedding)
        for hw in hw_ops:
            transpiled_qc.operations.append(hw)

        routing_gate_count += n_hw

        # ---- UPDATE EMBEDDING ----
        embedding[swap_q0], embedding[swap_q1] = embedding[swap_q1], embedding[swap_q0]

    # ================= FINALIZE =================
    for i, done in enumerate(executed):
        if not done:
            transpiled_qc.operations.append(operations[i])

    transpiled_qc.depth = transpiled_qc.calculate_depth()

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

    return transpiled_qc, embedding, metrics



# ---------------- DEBUG HELPER FUNCTIONS ----------------
def _analyze_circuit(qc: QuantumCircuit):
    gate_counts = defaultdict(int)
    qubit_pairs = defaultdict(int)
    for op in qc.operations:
        if isinstance(op, Operation) and hasattr(op, 'qubits'):
            gate_counts[op.name] += 1
            if len(op.qubits) == 2:
                q0, q1 = sorted(op.qubits)
                qubit_pairs[(q0, q1)] += 1
    if qubit_pairs:
        for (q0, q1), count in sorted(qubit_pairs.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  ({q0},{q1}): {count} gates")

def _build_dependencies_debug(operations):
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

def _get_front_layer_debug(executed, dependencies):
    front_layer = []
    for i in range(len(executed)):
        if not executed[i] and all(executed[dep] for dep in dependencies[i]):
            front_layer.append(i)
    return front_layer

def _build_adjacency_list(coupling_map):
    adj = defaultdict(set)
    for u, v in coupling_map:
        adj[u].add(v)
        adj[v].add(u)
    return adj

def _build_distance_matrix_fast(adjacency, num_qubits):
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

def _find_swap_for_gate(q0, q1, embedding, adjacency, distance_matrix, coupling_set):
    p0, p1 = embedding[q0], embedding[q1]
    current_dist = distance_matrix.get((p0, p1), 999999)
    if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
        return None
    best_swap = None
    best_improvement = -1
    for neighbor_p in adjacency.get(p0, []):
        for l, p in embedding.items():
            if p == neighbor_p and l != q0:
                temp_embedding = embedding.copy()
                temp_embedding[q0], temp_embedding[l] = temp_embedding[l], temp_embedding[q0]
                new_p0 = temp_embedding[q0]
                new_dist = distance_matrix.get((new_p0, p1), 999999)
                improvement = current_dist - new_dist
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = tuple(sorted([q0, l]))
    for neighbor_p in adjacency.get(p1, []):
        for l, p in embedding.items():
            if p == neighbor_p and l != q1:
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

def _find_random_swap_safe(embedding, adjacency):
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
