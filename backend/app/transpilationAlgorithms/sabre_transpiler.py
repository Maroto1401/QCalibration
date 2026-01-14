from typing import Dict, Tuple, List, Set, Optional
import random
import heapq
from collections import defaultdict, deque
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

# ---------------- DEBUGGABLE SABRE TRANSPILER ----------------
def sabre_transpiler(
    qc: QuantumCircuit,
    topology,
    use_trivial_embedding: bool = False,
    heuristic: str = "distance",
    max_swaps_per_gate: int = 10  # Safety limit
) -> Tuple[QuantumCircuit, Dict[int,int], Dict[str,float]]:
    print("SABRE: Starting transpilation ...")
    # Analyze circuit first
    _analyze_circuit(qc)
    
    # Build data structures
    coupling_set = build_coupling_set(topology.coupling_map)
    adjacency = _build_adjacency_list(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    
    # Simple initial embedding
    embedding = {i: i for i in range(qc.num_qubits)}
    
    # Build distance matrix
    distance_matrix = _build_distance_matrix_fast(adjacency, topology.numQubits)
    
    # Result circuit
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    
    # Track metrics
    gates_inserted = 0
    total_gate_error = 0.0
    total_duration = 0.0
    
    # Make copies of operations
    operations = list(qc.operations)
    num_gates = len(operations)
    
    # Track execution state
    dependencies = _build_dependencies_debug(operations)
    executed = [False] * num_gates
    execution_order = []
    
    # Track SWAPs per gate to avoid infinite loops
    swaps_per_gate = defaultdict(int)
    
    # Main execution loop
    iteration = 0
    consecutive_swaps = 0
    max_iterations = 10000
    
    
    while not all(executed) and iteration < max_iterations:
        iteration += 1
        
        # Get front layer
        front_layer = _get_front_layer_debug(executed, dependencies)
        
        if not front_layer:
            break
        
        # DEBUG: Print front layer
        if iteration <= 10 or iteration % 100 == 0:  # Only print first 10 and every 100th
            for idx in front_layer[:3]:  # Show first 3
                op = operations[idx]
                if isinstance(op, Operation) and hasattr(op, 'qubits'):
                    if len(op.qubits) == 2:
                        q0, q1 = op.qubits
                        p0, p1 = embedding[q0], embedding[q1]
                        connected = (p0, p1) in coupling_set or (p1, p0) in coupling_set
        
        # Try to execute gates in front layer
        executed_this_iteration = False
        
        for gate_idx in front_layer[:]:  # Copy to avoid modification issues
            if executed[gate_idx]:
                continue
                
            op = operations[gate_idx]
            
            # Non-gate operation
            if not isinstance(op, Operation) or not hasattr(op, 'qubits'):
                transpiled_qc.operations.append(op)
                executed[gate_idx] = True
                execution_order.append(gate_idx)
                executed_this_iteration = True
                consecutive_swaps = 0
                continue
            
            # Single-qubit gate - always executable
            if len(op.qubits) == 1:
                transpiled_qc.operations.append(op)
                executed[gate_idx] = True
                execution_order.append(gate_idx)
                executed_this_iteration = True
                consecutive_swaps = 0
                
                # Track metrics
                error, duration = track_single_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration
                continue
            
            # Two-qubit gate - check connectivity
            if len(op.qubits) == 2:
                q0, q1 = op.qubits
                p0, p1 = embedding[q0], embedding[q1]
                
                # Check if connected
                if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
                    # Can execute
                    transpiled_qc.operations.append(op)
                    executed[gate_idx] = True
                    execution_order.append(gate_idx)
                    executed_this_iteration = True
                    consecutive_swaps = 0
                    swaps_per_gate[gate_idx] = 0  # Reset counter
                    
                    # Track metrics
                    error, duration = track_two_qubit_gate(
                        op, embedding, gate_error_map, gate_duration_map
                    )
                    total_gate_error += error
                    total_duration += duration
                    
                    continue
                else:
                    # Gate is blocked
                    swaps_per_gate[gate_idx] += 1
                    
                    # Safety check: too many SWAPs for this gate
                    if swaps_per_gate[gate_idx] > max_swaps_per_gate:
                        transpiled_qc.operations.append(op)
                        executed[gate_idx] = True
                        execution_order.append(gate_idx)
                        executed_this_iteration = True
                        consecutive_swaps = 0
                        continue
        
        # If we executed gates, continue to next iteration
        if executed_this_iteration:
            continue
        
        # If no gates executed, we need SWAPs
        consecutive_swaps += 1
        
        if consecutive_swaps > 50:
            print(f"[SABRE DEBUG] ERROR: Too many consecutive SWAPs ({consecutive_swaps})")
            for idx in front_layer[:5]:
                op = operations[idx]
                if isinstance(op, Operation) and hasattr(op, 'qubits') and len(op.qubits) == 2:
                    q0, q1 = op.qubits
                    p0, p1 = embedding[q0], embedding[q1]
                    dist = distance_matrix.get((p0, p1), 999999)
                    print(f"  Gate {idx}: ({q0},{q1}) -> ({p0},{p1}), distance: {dist}")
            break
        
        # Find the most critical blocked gate
        blocked_gates = []
        for idx in front_layer:
            op = operations[idx]
            if isinstance(op, Operation) and hasattr(op, 'qubits') and len(op.qubits) == 2:
                q0, q1 = op.qubits
                p0, p1 = embedding[q0], embedding[q1]
                if not ((p0, p1) in coupling_set or (p1, p0) in coupling_set):
                    dist = distance_matrix.get((p0, p1), 999999)
                    blocked_gates.append((idx, q0, q1, dist))
        
        if not blocked_gates:
            break
        
        # Sort by distance (most critical first)
        blocked_gates.sort(key=lambda x: x[3], reverse=True)
        most_critical = blocked_gates[0]
        crit_idx, crit_q0, crit_q1, crit_dist = most_critical
        
        
        # Find a SWAP that reduces distance for critical gate
        best_swap = _find_swap_for_gate(crit_q0, crit_q1, embedding, adjacency, distance_matrix, coupling_set)
        
        if best_swap is None:
            best_swap = _find_random_swap_safe(embedding, adjacency)
        
        if best_swap is None:
            break
        
        # Insert the SWAP
        swap_q0, swap_q1 = best_swap
        swap_op = Operation(name="swap", qubits=[swap_q0, swap_q1])
        transpiled_qc.operations.append(swap_op)
        gates_inserted += 1
        
        # Update metrics
        p0, p1 = embedding[swap_q0], embedding[swap_q1]
        swap_error = estimate_swap_error(p0, p1, gate_error_map)
        cx_duration = get_gate_duration("cx", [p0, p1], gate_duration_map)
        total_gate_error += swap_error
        total_duration += 3 * cx_duration
        
        # Update embedding
        embedding[swap_q0], embedding[swap_q1] = embedding[swap_q1], embedding[swap_q0]
        
        
        # Check if SWAP helped
        new_p0, new_p1 = embedding[crit_q0], embedding[crit_q1]
        new_dist = distance_matrix.get((new_p0, new_p1), 999999)
    
    # Finalization
    executed_count = sum(executed)
    print(f"\n[SABRE] ====== FINAL RESULTS ======")
    print(f"[SABRE] Executed {executed_count}/{num_gates} gates")
    print(f"[SABRE] Inserted {gates_inserted} SWAPs")
    print(f"[SABRE] Iterations: {iteration}")
    
    # Add any unexecuted gates (shouldn't happen but safety)
    if executed_count < num_gates:
        for i in range(num_gates):
            if not executed[i]:
                transpiled_qc.operations.append(operations[i])
    
    transpiled_qc.depth = transpiled_qc.calculate_depth()
    
    # Calculate metrics
    metrics = calculate_circuit_metrics(
        original_qc=qc,
        transpiled_qc=transpiled_qc,
        gates_inserted=gates_inserted,
        total_gate_error=total_gate_error,
        total_duration=total_duration,
        embedding=embedding,
        topology=topology,
    )
    
    metrics['swap_count'] = gates_inserted
    metrics['iterations'] = iteration
    metrics['execution_ratio'] = executed_count / num_gates if num_gates > 0 else 0
    
    print(f"[SABRE] Transpiled circuit has {len(transpiled_qc.operations)} operations")
    print(f"[SABRE] Original had {num_gates} operations")
    
    return transpiled_qc, embedding, metrics


# ---------------- DEBUG HELPER FUNCTIONS ----------------

def _analyze_circuit(qc: QuantumCircuit):
    """Analyze the circuit to understand its structure."""
    
    # Count gate types
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
    """Build dependency graph with debugging."""
    num_ops = len(operations)
    dependencies = [set() for _ in range(num_ops)]
    last_gate_on_qubit = {}
    
    for idx, op in enumerate(operations):
        if isinstance(op, Operation) and hasattr(op, 'qubits'):
            for q in op.qubits:
                if q in last_gate_on_qubit:
                    dependencies[idx].add(last_gate_on_qubit[q])
                last_gate_on_qubit[q] = idx
    
    # Debug: check for complex dependencies
    max_deps = max(len(d) for d in dependencies) if dependencies else 0
    
    return dependencies


def _get_front_layer_debug(executed, dependencies):
    """Get front layer with debugging."""
    front_layer = []
    for i in range(len(executed)):
        if not executed[i] and all(executed[dep] for dep in dependencies[i]):
            front_layer.append(i)
    return front_layer


def _build_adjacency_list(coupling_map):
    """Build adjacency list."""
    adj = defaultdict(set)
    for u, v in coupling_map:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _build_distance_matrix_fast(adjacency, num_qubits):
    """BFS-based distance matrix."""
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
    """Find SWAP that reduces distance between q0 and q1."""
    p0, p1 = embedding[q0], embedding[q1]
    current_dist = distance_matrix.get((p0, p1), 999999)
    
    # Already connected?
    if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
        return None
    
    best_swap = None
    best_improvement = -1
    
    # Consider SWAPs involving q0
    for neighbor_p in adjacency.get(p0, []):
        # Find logical qubit at this location
        for l, p in embedding.items():
            if p == neighbor_p and l != q0:
                # Try this SWAP
                temp_embedding = embedding.copy()
                temp_embedding[q0], temp_embedding[l] = temp_embedding[l], temp_embedding[q0]
                new_p0 = temp_embedding[q0]
                new_dist = distance_matrix.get((new_p0, p1), 999999)
                
                improvement = current_dist - new_dist
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = tuple(sorted([q0, l]))
    
    # Consider SWAPs involving q1
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
    
    # Only return if improvement is positive
    if best_improvement > 0:
        return best_swap
    
    return None


def _find_random_swap_safe(embedding, adjacency):
    """Find a random valid SWAP."""
    physical_to_logical = {}
    for l, p in embedding.items():
        physical_to_logical[p] = l
    
    # Get all possible SWAPs
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