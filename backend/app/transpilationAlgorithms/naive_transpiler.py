from typing import Dict, Tuple, Optional
from collections import deque, defaultdict
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..utils.transpilation_utils import (
    build_calibration_maps,
    calculate_circuit_metrics,
    track_single_qubit_gate,
    track_two_qubit_gate,
    estimate_swap_error,
    get_gate_duration,
    is_connected
)

def _build_undirected_coupling(coupling_map):
    """Build adjacency list representation for faster lookup."""
    adjacency = defaultdict(set)
    for u, v in coupling_map:
        adjacency[u].add(v)
        adjacency[v].add(u)
    return adjacency

def _shortest_path(adjacency, start, end):
    """Find shortest path using BFS with adjacency list."""
    if start == end:
        return [start]
    
    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        node = path[-1]

        # Check all neighbors efficiently
        for neighbor in adjacency.get(node, set()):
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    # No path found
    return None

def naive_transpiler(
    qc: QuantumCircuit,
    topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:

    print("[DEBUG] Starting naive transpiler")

    # Identity embedding
    embedding = {i: i for i in range(qc.num_qubits)}
    print(f"[DEBUG] Initial embedding: {embedding}")

    # Track ALL physical qubits used (including ancillas)
    physical_qubits_used = set(embedding.values())  # Start with initial mapping
    
    # UNDIRECTED coupling graph (adjacency list)
    coupling_adjacency = _build_undirected_coupling(topology.coupling_map)
    
    # Get all physical qubits in topology
    all_physical_qubits = set()
    for u, v in topology.coupling_map:
        all_physical_qubits.add(u)
        all_physical_qubits.add(v)
    
    max_physical_qubit = max(all_physical_qubits) if all_physical_qubits else -1
    print(f"[DEBUG] Topology: {len(all_physical_qubits)} qubits, max qubit: {max_physical_qubit}")
    
    # Validate topology can support circuit at least for initial embedding
    if qc.num_qubits - 1 > max_physical_qubit:
        raise ValueError(
            f"Circuit requires {qc.num_qubits} qubits (0-{qc.num_qubits-1}), "
            f"but topology only has qubits up to {max_physical_qubit}. "
            f"The identity embedding cannot be used."
        )
    
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    gates_inserted = 0
    total_gate_error = 0.0
    total_duration = 0.0

    # Logical → physical mapping
    physical_pos = embedding.copy()  # logical -> physical
    
    # Physical → logical mapping
    logical_at_physical = {}
    for logical, physical in embedding.items():
        logical_at_physical[physical] = logical
    
    # Helper function to get logical qubit at a physical location
    def get_logical_at_physical(physical):
        return logical_at_physical.get(physical)

    # Helper function to update mappings after swap
    def apply_swap(logical1, logical2, physical1, physical2):
        physical_pos[logical1] = physical2
        physical_pos[logical2] = physical1
        logical_at_physical[physical1] = logical2
        logical_at_physical[physical2] = logical1
        
        # Track both physical qubits as used
        physical_qubits_used.add(physical1)
        physical_qubits_used.add(physical2)

    for idx, op in enumerate(qc.operations):
        print(f"\n[DEBUG] Processing op {idx}: {op}")

        if not isinstance(op, Operation):
            transpiled_qc.operations.append(op)
            continue

        # SINGLE-QUBIT
        if len(op.qubits) == 1:
            transpiled_qc.operations.append(op)
            error, duration = track_single_qubit_gate(
                op, physical_pos, gate_error_map, gate_duration_map
            )
            total_gate_error += error
            total_duration += duration
            print(f"[DEBUG] 1Q gate → error={error}, duration={duration}")
            
            # Track the physical qubit used
            logical_q = op.qubits[0]
            physical_q = physical_pos[logical_q]
            physical_qubits_used.add(physical_q)

        # TWO-QUBIT
        elif len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = physical_pos[q0], physical_pos[q1]
            print(f"[DEBUG] 2Q gate {op.name} logical({q0},{q1}) physical({p0},{p1})")
            
            # Track both physical qubits as used
            physical_qubits_used.add(p0)
            physical_qubits_used.add(p1)

            if p1 in coupling_adjacency.get(p0, set()):
                print("[DEBUG] Qubits already connected")
                transpiled_qc.operations.append(op)
                error, duration = track_two_qubit_gate(
                    op, physical_pos, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration
            else:
                print(f"[DEBUG] Routing required (move-there-and-back) from physical {p0} to {p1}")

                path = _shortest_path(coupling_adjacency, p0, p1)
                
                if path is None:
                    error_msg = (
                        f"No routing path exists between physical qubits {p0} and {p1} "
                        f"(logical qubits {q0} and {q1}). "
                        f"The topology does not support this circuit with identity embedding."
                    )
                    print(f"[ERROR] {error_msg}")
                    raise RuntimeError(error_msg)
                
                print(f"[DEBUG] Path found: {path}")
                
                # Track ALL physical qubits in the path as used
                for physical_q in path:
                    physical_qubits_used.add(physical_q)
                
                # Save the state before routing
                saved_physical_pos = physical_pos.copy()
                saved_logical_at_physical = logical_at_physical.copy()
                
                # Move logical qubit q0 along the path to meet q1
                moving_logical = q0
                current_physical = p0

                # Forward pass: move q0 to be adjacent to q1
                for i in range(len(path) - 1):
                    next_physical = path[i + 1]
                    
                    # Track both qubits as used
                    physical_qubits_used.add(current_physical)
                    physical_qubits_used.add(next_physical)
                    
                    # Check what logical qubit is at the next physical location
                    neighbor_logical = get_logical_at_physical(next_physical)
                    
                    # If the next physical qubit is empty, we just move there
                    if neighbor_logical is None:
                        print(f"[DEBUG] MOVE logical({moving_logical}) from physical({current_physical}) to empty physical({next_physical})")
                        
                        # Update mappings
                        old_physical = current_physical
                        physical_pos[moving_logical] = next_physical
                        logical_at_physical[next_physical] = moving_logical
                        if old_physical in logical_at_physical:
                            del logical_at_physical[old_physical]
                        
                        current_physical = next_physical
                        continue
                    
                    # If there's a logical qubit at next_physical, we need to SWAP
                    swap_op = Operation(name="swap", qubits=[moving_logical, neighbor_logical])
                    transpiled_qc.operations.append(swap_op)
                    gates_inserted += 1

                    # SWAP metrics
                    swap_error = estimate_swap_error(current_physical, next_physical, gate_error_map)
                    cx_duration = get_gate_duration("cx", [current_physical, next_physical], gate_duration_map)
                    total_gate_error += swap_error
                    total_duration += 3 * cx_duration

                    # Apply the swap in our mappings
                    apply_swap(moving_logical, neighbor_logical, current_physical, next_physical)
                    
                    print(f"[DEBUG] SWAP logical({moving_logical},{neighbor_logical}) physical({current_physical},{next_physical})")
                    
                    current_physical = next_physical

                # Now q0 and q1 should be adjacent
                p0_final = physical_pos[q0]
                p1_final = physical_pos[q1]
                
                if p1_final not in coupling_adjacency.get(p0_final, set()):
                    print(f"[ERROR] After routing, qubits {p0_final} and {p1_final} are not connected!")
                    raise RuntimeError("Routing failed to make qubits adjacent")
                
                # Perform the 2Q gate
                print("[DEBUG] Applying routed 2Q gate")
                transpiled_qc.operations.append(op)
                error, duration = track_two_qubit_gate(
                    op, physical_pos, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration

                # Reverse pass: move q0 back to original position
                moving_logical = q0
                current_physical = p0_final
                
                for i in range(len(path) - 1, 0, -1):
                    prev_physical = path[i - 1]
                    
                    # Track both qubits as used
                    physical_qubits_used.add(current_physical)
                    physical_qubits_used.add(prev_physical)
                    
                    # Check what logical qubit is at the previous physical location
                    neighbor_logical = get_logical_at_physical(prev_physical)
                    
                    # If prev_physical is empty, just move there
                    if neighbor_logical is None:
                        print(f"[DEBUG] MOVE BACK logical({moving_logical}) from physical({current_physical}) to empty physical({prev_physical})")
                        
                        # Update mappings
                        old_physical = current_physical
                        physical_pos[moving_logical] = prev_physical
                        logical_at_physical[prev_physical] = moving_logical
                        if old_physical in logical_at_physical:
                            del logical_at_physical[old_physical]
                        
                        current_physical = prev_physical
                        continue
                    
                    # SWAP with whatever is at prev_physical
                    swap_op = Operation(name="swap", qubits=[moving_logical, neighbor_logical])
                    transpiled_qc.operations.append(swap_op)
                    gates_inserted += 1

                    swap_error = estimate_swap_error(current_physical, prev_physical, gate_error_map)
                    cx_duration = get_gate_duration("cx", [current_physical, prev_physical], gate_duration_map)
                    total_gate_error += swap_error
                    total_duration += 3 * cx_duration

                    apply_swap(moving_logical, neighbor_logical, current_physical, prev_physical)
                    
                    print(f"[DEBUG] Undo SWAP logical({moving_logical},{neighbor_logical}) physical({current_physical},{prev_physical})")
                    
                    current_physical = prev_physical

                if physical_pos != saved_physical_pos:
                    print(f"[WARNING] Mapping mismatch after undo!")
                    print(f"Expected: {saved_physical_pos}")
                    print(f"Got: {physical_pos}")
                    physical_pos = saved_physical_pos.copy()
                    logical_at_physical = saved_logical_at_physical.copy()

        else:
            raise NotImplementedError(
                f"Gate {op.name} with {len(op.qubits)} qubits not supported"
            )

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
    
    # Add physical qubits used to metrics
    metrics['physical_qubits_used'] = len(physical_qubits_used)
    metrics['physical_qubits_list'] = sorted(list(physical_qubits_used))
    metrics['ancilla_qubits'] = len(physical_qubits_used) - len(set(embedding.values()))
    metrics['ancilla_qubits_list'] = sorted(list(physical_qubits_used - set(embedding.values())))

    print(f"[DEBUG] Transpilation finished")
    print(f"[DEBUG] Physical qubits used: {len(physical_qubits_used)}")
    print(f"[DEBUG] Ancilla qubits used: {metrics['ancilla_qubits']}")

    return transpiled_qc, embedding, metrics