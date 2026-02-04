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
    """Find shortest path between two physical qubits using BFS"""
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

# --- Greedy embedding search ---
def greedy_find_embedding(
    qc: QuantumCircuit,
    topology: Topology
) -> Dict[int, int]:
    """
    Find a simple greedy embedding for the circuit.
    Uses identity embedding if circuit fits, otherwise tries to find a valid one.
    
    Returns: {logical_qubit: physical_qubit}
    """
    num_logical_qubits = qc.num_qubits
    num_physical_qubits = topology.numQubits

    if num_logical_qubits > num_physical_qubits:
        raise RuntimeError(
            f"Circuit has {num_logical_qubits} qubits but topology only has {num_physical_qubits}"
        )

    # Try identity embedding first (simplest case)
    embedding = {i: i for i in range(num_logical_qubits)}
    
    # Check if identity embedding is valid (all physical qubits exist)
    if all(p < num_physical_qubits for p in embedding.values()):
        print(f"[NAIVE] Using identity embedding: {embedding}")
        return embedding

    # If identity doesn't work, use consecutive physical qubits
    embedding = {i: i for i in range(num_logical_qubits)}
    print(f"[NAIVE] Using consecutive embedding: {embedding}")
    return embedding

# --- Check if embedding is valid ---
def is_embedding_valid(embedding: Dict[int, int], topology: Topology) -> bool:
    """Check if all physical qubits in embedding exist in topology"""
    return all(p < topology.numQubits for p in embedding.values())

# --- Check if two-qubit gate can be executed without routing ---
def can_execute_gate(q0: int, q1: int, embedding: Dict[int, int], coupling_adjacency: dict) -> bool:
    """Check if logical qubits q0, q1 can execute a two-qubit gate directly"""
    p0 = embedding[q0]
    p1 = embedding[q1]
    return p1 in coupling_adjacency[p0]

# --- Find routing path and required SWAPs ---
def find_routing_path(
    q0: int, 
    q1: int, 
    embedding: Dict[int, int], 
    coupling_adjacency: dict
) -> Tuple[list, list[Tuple[int, int]]]:
    """
    Find path to route logical qubits q0 and q1 to adjacent positions.
    
    Returns:
        - path: physical qubit path from p0 to p1
        - swaps: list of (p_a, p_b) pairs representing SWAPs to perform
    """
    p0 = embedding[q0]
    p1 = embedding[q1]

    if p1 in coupling_adjacency[p0]:
        return [p0, p1], []

    # Find shortest path
    path = _shortest_path(coupling_adjacency, p0, p1)
    if path is None:
        raise RuntimeError(f"No path between physical qubits {p0} and {p1}")

    # SWAPs needed: between consecutive qubits in path
    swaps = []
    for i in range(len(path) - 1):
        swaps.append((path[i], path[i + 1]))

    return path, swaps

# --- Track qubit position through a SWAP ---
def track_qubit_through_swap(qubit_pos: int, swap_a: int, swap_b: int) -> int:
    """
    After a SWAP(swap_a, swap_b), return new position of qubit that was at qubit_pos.
    
    SWAP exchanges data at positions swap_a and swap_b.
    """
    if qubit_pos == swap_a:
        return swap_b
    elif qubit_pos == swap_b:
        return swap_a
    else:
        return qubit_pos

# ---------------------------------------------------------------------
#                    STATIC EMBEDDING NAIVE TRANSPILER (CORRECTED)
# ---------------------------------------------------------------------
def naive_transpiler(
    qc: QuantumCircuit,
    topology: Topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:
    """
    Naive transpiler with STATIC embedding and proper qubit position tracking.
    
    Algorithm:
    1. Find a fixed embedding at the start
    2. For each two-qubit gate:
       - If qubits are adjacent in topology: execute directly
       - Else:
         a) Forward SWAPs: Insert SWAPs to route them to adjacent positions
            Track actual positions after each SWAP
         b) Execute gate at CURRENT physical positions (after forward routing)
         c) Backward SWAPs: Undo SWAPs in reverse order
            Track positions again to restore original embedding
    3. Embedding logically remains constant (but positions temporarily change)
    
    KEY FIX: Track qubit positions through all SWAPs, apply gate at current positions.
    """

    print("[NAIVE] Starting static embedding naive transpiler (corrected)")

    # ========== STEP 1: FIND FIXED EMBEDDING ==========
    embedding = greedy_find_embedding(qc, topology)
    
    if not is_embedding_valid(embedding, topology):
        raise RuntimeError(f"Invalid embedding: {embedding} for topology with {topology.numQubits} qubits")

    coupling_adjacency = _build_undirected_coupling(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    # Initialize transpiled circuit
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    # Track metrics
    logical_swap_count = 0          # Number of logical SWAPs performed
    routing_gate_count = 0          # Physical gates added for routing

    print(f"[NAIVE] Fixed embedding: {embedding}")

    # ========== MAIN LOOP ==========
    for op_idx, op in enumerate(qc.operations):
        if not isinstance(op, Operation):
            # Pass through non-Operation objects (barriers, etc.)
            transpiled_qc.operations.append(op)
            continue

        # ---------- SINGLE-QUBIT GATES ----------
        if len(op.qubits) == 1:
            q0 = op.qubits[0]
            p0 = embedding[q0]  # Physical position (FIXED)

            # Create operation with physical qubit
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
                phys_op, embedding, gate_error_map, gate_duration_map
            )
        # ---------- TWO-QUBIT GATES ----------
        elif len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]

            # Check if qubits are already adjacent
            if can_execute_gate(q0, q1, embedding, coupling_adjacency):                
                # Apply gate with fixed physical qubits
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
                    phys_op, embedding, gate_error_map, gate_duration_map
                )
                continue

            # NOT adjacent - need to route and unroute
            
            path, swaps = find_routing_path(q0, q1, embedding, coupling_adjacency)

            # Track temporary positions as we route (CRITICAL!)
            temp_p0 = p0
            temp_p1 = p1

            # ---- FORWARD ROUTING: Insert SWAPs to bring qubits to adjacent positions ----
            for swap_idx, (swap_a, swap_b) in enumerate(swaps):
                logical_swap_count += 1
                swap_ops = swap_decomposition(swap_a, swap_b)
                routing_gate_count += len(swap_ops)

                for sop in swap_ops:
                    transpiled_qc.operations.append(sop)

                # CRITICAL: Track where q0 and q1 move to after this SWAP
                temp_p0 = track_qubit_through_swap(temp_p0, swap_a, swap_b)
                temp_p1 = track_qubit_through_swap(temp_p1, swap_a, swap_b)

            # Now apply the gate at CURRENT (temporary) physical positions
            phys_op = Operation(
                name=op.name,
                qubits=[temp_p0, temp_p1],  # ← Use current positions after routing!
                params=op.params,
                clbits=op.clbits,
                condition=op.condition,
                metadata=op.metadata
            )
            transpiled_qc.operations.append(phys_op)
            
            err, dur = track_two_qubit_gate(
                phys_op, embedding, gate_error_map, gate_duration_map
            )

            # ---- BACKWARD ROUTING: Undo SWAPs in reverse order to restore original positions ----
            for swap_idx, (swap_a, swap_b) in enumerate(reversed(swaps)):
                logical_swap_count += 1
                swap_ops = swap_decomposition(swap_a, swap_b)
                routing_gate_count += len(swap_ops)

                for sop in swap_ops:
                    transpiled_qc.operations.append(sop)

                # Track positions again as we undo SWAPs
                temp_p0 = track_qubit_through_swap(temp_p0, swap_a, swap_b)
                temp_p1 = track_qubit_through_swap(temp_p1, swap_a, swap_b)

        else:
            raise NotImplementedError(
                f"Gate {op.name} with {len(op.qubits)} qubits not supported"
            )

    # ========== FINALIZE ==========
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
    })

    print(f"\n[NAIVE] Transpilation finished")
    print(f"[NAIVE] Fixed embedding: {embedding}")
    print(f"[NAIVE] Logical SWAPs: {logical_swap_count}")
    print(f"[NAIVE] Routing gates added: {routing_gate_count}")
    print(f"[NAIVE] Total transpiled operations: {len(transpiled_qc.operations)}")

    return transpiled_qc, embedding, metrics