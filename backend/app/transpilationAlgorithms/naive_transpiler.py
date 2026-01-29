from typing import Dict, Tuple
from collections import deque, defaultdict
import math

from ..core.BaseModelClasses import Topology
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..utils.transpilation_utils import (
    build_calibration_maps,
    calculate_circuit_metrics,
    track_single_qubit_gate,
    track_two_qubit_gate,
    get_gate_duration
)

# --- Helper: adjacency + shortest path ---
def _build_undirected_coupling(coupling_map):
    adjacency = defaultdict(set)
    for u, v in coupling_map:
        adjacency[u].add(v)
        adjacency[v].add(u)
    return adjacency

def _shortest_path(adjacency, start, end):
    if start == end:
        return [start]

    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        node = path[-1]

        for neighbor in adjacency.get(node, set()):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None

# --- CX decomposition (basis: rz, sx, cz) ---
def cx_decomposition(control: int, target: int) -> list[Operation]:
    ops = []

    # H on target
    ops.append(Operation("rz", [target], [math.pi]))
    ops.append(Operation("sx", [target]))
    ops.append(Operation("rz", [target], [math.pi]))

    ops.append(Operation("cz", [control, target]))

    # H on target
    ops.append(Operation("rz", [target], [math.pi]))
    ops.append(Operation("sx", [target]))
    ops.append(Operation("rz", [target], [math.pi]))

    return ops

# --- SWAP = 3 CX ---
def swap_decomposition(q0: int, q1: int) -> list[Operation]:
    ops = []
    ops.extend(cx_decomposition(q0, q1))
    ops.extend(cx_decomposition(q1, q0))
    ops.extend(cx_decomposition(q0, q1))
    return ops

# ---------------------------------------------------------------------
#                           NAIVE TRANSPILER
# ---------------------------------------------------------------------
def naive_transpiler(
    qc: QuantumCircuit,
    topology: Topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:

    print("[NAIVE] Starting naive transpiler")

    # Identity embedding
    embedding = {i: i for i in range(qc.num_qubits)}
    coupling_adjacency = _build_undirected_coupling(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

     # Initialize transpiled circuit
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    # ---------------- CORRECT METRICS ----------------
    logical_swap_count = 0          # routing decisions
    routing_gate_count = 0          # physical gates added
    total_gate_error = 0.0
    total_duration = 0.0
    # -------------------------------------------------

    # Logical → physical maps
    physical_pos = embedding.copy()
    logical_at_physical = {v: k for k, v in embedding.items()}
    print("[NAIVE] Initial embedding: Done")
    def get_logical_at_physical(p):
        return logical_at_physical.get(p)

    def apply_swap(l0, l1, p0, p1):
        physical_pos[l0], physical_pos[l1] = p1, p0
        logical_at_physical[p0], logical_at_physical[p1] = l1, l0

    # ---------------- MAIN LOOP ----------------
    for op in qc.operations:
        if not isinstance(op, Operation):
            transpiled_qc.operations.append(op)
            continue

        # SINGLE-QUBIT
        if len(op.qubits) == 1:
            transpiled_qc.operations.append(op)
            err, dur = track_single_qubit_gate(
                op, physical_pos, gate_error_map, gate_duration_map
            )
            total_gate_error += err
            total_duration += dur

        # TWO-QUBIT
        elif len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = physical_pos[q0], physical_pos[q1]

            # Already connected
            if p1 in coupling_adjacency[p0]:
                transpiled_qc.operations.append(op)
                err, dur = track_two_qubit_gate(
                    op, physical_pos, gate_error_map, gate_duration_map
                )
                total_gate_error += err
                total_duration += dur
                continue

            # Route via shortest path
            path = _shortest_path(coupling_adjacency, p0, p1)
            if path is None:
                raise RuntimeError(f"No path between {p0} and {p1}")

            saved_phys = physical_pos.copy()
            saved_log = logical_at_physical.copy()

            moving_logical = q0
            current_physical = p0

            # ---- Forward swaps ----
            for i in range(len(path) - 1):
                next_physical = path[i + 1]
                neighbor_logical = get_logical_at_physical(next_physical)

                if neighbor_logical is None:
                    physical_pos[moving_logical] = next_physical
                    logical_at_physical[next_physical] = moving_logical
                    del logical_at_physical[current_physical]
                    current_physical = next_physical
                    continue

                logical_swap_count += 1
                swap_ops = swap_decomposition(current_physical, next_physical)
                routing_gate_count += len(swap_ops)

                for sop in swap_ops:
                    transpiled_qc.operations.append(sop)

                apply_swap(moving_logical, neighbor_logical,
                           current_physical, next_physical)
                current_physical = next_physical

            # Execute gate
            transpiled_qc.operations.append(op)
            err, dur = track_two_qubit_gate(
                op, physical_pos, gate_error_map, gate_duration_map
            )
            total_gate_error += err
            total_duration += dur

            # ---- Reverse swaps ----
            for i in range(len(path) - 1, 0, -1):
                prev_physical = path[i - 1]
                neighbor_logical = get_logical_at_physical(prev_physical)

                if neighbor_logical is None:
                    physical_pos[moving_logical] = prev_physical
                    logical_at_physical[prev_physical] = moving_logical
                    del logical_at_physical[current_physical]
                    current_physical = prev_physical
                    continue

                logical_swap_count += 1
                swap_ops = swap_decomposition(current_physical, prev_physical)
                routing_gate_count += len(swap_ops)

                for sop in swap_ops:
                    transpiled_qc.operations.append(sop)

                apply_swap(moving_logical, neighbor_logical,
                           current_physical, prev_physical)
                current_physical = prev_physical

            # Restore original embedding
            physical_pos = saved_phys
            logical_at_physical = saved_log

        else:
            raise NotImplementedError(
                f"Gate {op.name} with {len(op.qubits)} qubits not supported"
            )
    # ---------------- FINALIZE ----------------
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
    })

    print("[NAIVE] Transpilation finished")
    return transpiled_qc, embedding, metrics
