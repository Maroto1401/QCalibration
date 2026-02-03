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
)

PI = math.pi

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
    """Decompose CX into basis gates: H[t] CZ(c,t) H[t] where H = SX RZ(π/2) SX"""
    ops = []

    # First H on target: SX RZ(π/2) SX
    ops.append(Operation("sx", qubits=[target]))
    ops.append(Operation("rz", qubits=[target], params=[PI/2]))
    ops.append(Operation("sx", qubits=[target]))

    # CZ
    ops.append(Operation("cz", qubits=[control, target]))

    # Second H on target: SX RZ(π/2) SX
    ops.append(Operation("sx", qubits=[target]))
    ops.append(Operation("rz", qubits=[target], params=[PI/2]))
    ops.append(Operation("sx", qubits=[target]))

    return ops

# --- SWAP = 3 CX ---
def swap_decomposition(q0: int, q1: int) -> list[Operation]:
    """Decompose SWAP into 3 CX gates: CX(q0,q1) CX(q1,q0) CX(q0,q1)"""
    ops = []
    ops.extend(cx_decomposition(q0, q1))
    ops.extend(cx_decomposition(q1, q0))
    ops.extend(cx_decomposition(q0, q1))
    return ops

# ---------------------------------------------------------------------
#                      CORRECTED DYNAMIC TRANSPILER
# ---------------------------------------------------------------------
def dynamic_transpiler(
    qc: QuantumCircuit,
    topology: Topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:
    """
    DYNAMIC transpiler with corrected physical qubit tracking.
    
    Key fix: Apply gates to PHYSICAL qubits (current positions after routing),
    not to logical qubits. The embedding evolves as we route.
    """

    print("[DYNAMIC] Starting corrected DYNAMIC transpiler")

    # Initial embedding: logical qubit i is at physical qubit i
    embedding = {i: i for i in range(qc.num_qubits)}
    coupling_adjacency = _build_undirected_coupling(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    # Initialize transpiled circuit
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    # Track metrics
    logical_swap_count = 0          # Number of logical SWAPs performed
    routing_gate_count = 0          # Physical gates added for routing
    total_gate_error = 0.0
    total_duration = 0.0

    # ========== CRITICAL: These track the CURRENT state, not initial ==========
    # physical_pos[logical_q] = where logical qubit q currently is (physically)
    physical_pos = embedding.copy()
    
    # logical_at_physical[physical_q] = which logical qubit is at physical position q
    logical_at_physical = {v: k for k, v in embedding.items()}
    # ===========================================================================

    print("[DYNAMIC] Initial embedding:", embedding)
    print("[DYNAMIC] Initial physical_pos:", physical_pos)

    def get_logical_at_physical(p):
        """Get which logical qubit is at physical position p"""
        return logical_at_physical.get(p)

    def apply_swap(l0, l1, p0, p1):
        """
        Execute a logical swap between logical qubits l0 and l1.
        They are currently at physical positions p0 and p1.
        After swap: l0 is at p1, l1 is at p0.
        """
        physical_pos[l0], physical_pos[l1] = p1, p0
        logical_at_physical[p0], logical_at_physical[p1] = l1, l0

    # ========== MAIN LOOP ==========
    for op_idx, op in enumerate(qc.operations):
        if not isinstance(op, Operation):
            # Pass through non-Operation objects (barriers, etc.)
            transpiled_qc.operations.append(op)
            continue

        # ---------- SINGLE-QUBIT GATES ----------
        if len(op.qubits) == 1:
            q0 = op.qubits[0]
            p0 = physical_pos[q0]  # Get current physical position

            # Create operation with PHYSICAL qubit
            phys_op = Operation(
                name=op.name,
                qubits=[p0],
                params=op.params,
                clbits=op.clbits,
                condition=op.condition,
                metadata=op.metadata
            )
            transpiled_qc.operations.append(phys_op)
            
            err, dur = track_single_qubit_gate(
                phys_op, physical_pos, gate_error_map, gate_duration_map
            )
            total_gate_error += err
            total_duration += dur

        # ---------- TWO-QUBIT GATES ----------
        elif len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = physical_pos[q0], physical_pos[q1]

            # Check if qubits are adjacent
            if p1 in coupling_adjacency[p0]:                
                # Apply gate with CURRENT physical qubits
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0, p1],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata
                )
                transpiled_qc.operations.append(phys_op)
                
                err, dur = track_two_qubit_gate(
                    phys_op, physical_pos, gate_error_map, gate_duration_map
                )
                total_gate_error += err
                total_duration += dur
                continue

            # NOT adjacent - need to route            
            path = _shortest_path(coupling_adjacency, p0, p1)
            if path is None:
                raise RuntimeError(f"No path between physical qubits {p0} and {p1}")

            print(f"        Path: {path}")

            # ---- Route q0 along the path to q1 ----
            moving_logical = q0
            current_physical = p0

            for i in range(len(path) - 1):
                next_physical = path[i + 1]
                neighbor_logical = get_logical_at_physical(next_physical)

                if neighbor_logical is None:
                    # Next position is empty, just move
                    physical_pos[moving_logical] = next_physical
                    logical_at_physical[next_physical] = moving_logical
                    if current_physical in logical_at_physical:
                        del logical_at_physical[current_physical]
                    current_physical = next_physical
                    continue

                # Next position is occupied - need to SWAP
                logical_swap_count += 1

                # Add SWAP gates at PHYSICAL positions
                swap_ops = swap_decomposition(current_physical, next_physical)
                routing_gate_count += len(swap_ops)

                for sop in swap_ops:
                    transpiled_qc.operations.append(sop)

                # Update tracking: swap the logical qubits
                apply_swap(moving_logical, neighbor_logical, current_physical, next_physical)
                current_physical = next_physical

            # Now q0 and q1 are adjacent. Get their current physical positions
            p0 = physical_pos[q0]
            p1 = physical_pos[q1]

            # Apply the gate with CURRENT physical positions
            phys_op = Operation(
                name=op.name,
                qubits=[p0, p1],
                params=op.params,
                clbits=op.clbits,
                condition=op.condition,
                metadata=op.metadata
            )
            transpiled_qc.operations.append(phys_op)

            err, dur = track_two_qubit_gate(
                phys_op, physical_pos, gate_error_map, gate_duration_map
            )
            total_gate_error += err
            total_duration += dur

        else:
            raise NotImplementedError(
                f"Gate {op.name} with {len(op.qubits)} qubits not supported"
            )

    # ========== FINALIZE ==========
    transpiled_qc.depth = transpiled_qc.calculate_depth()

    # Extract final embedding from physical_pos
    final_embedding = physical_pos.copy()

    metrics = calculate_circuit_metrics(
        original_qc=qc,
        transpiled_qc=transpiled_qc,
        logical_swap_count=logical_swap_count,
        embedding=final_embedding,
        topology=topology,
    )

    metrics.update({
        "routing_gate_count": routing_gate_count,
        "total_physical_gates": len(transpiled_qc.operations),
    })

    print(f"\n[DYNAMIC] Transpilation finished")
    print(f"[DYNAMIC] Final embedding: {final_embedding}")
    print(f"[DYNAMIC] Logical SWAPs: {logical_swap_count}")
    print(f"[DYNAMIC] Routing gates added: {routing_gate_count}")
    print(f"[DYNAMIC] Total transpiled operations: {len(transpiled_qc.operations)}")

    return transpiled_qc, final_embedding, metrics