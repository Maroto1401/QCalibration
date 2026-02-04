import math
from typing import Dict, Tuple
import random
from collections import defaultdict, deque
from ..core.QuantumCircuit import QuantumCircuit, Operation
from ..core.BaseModelClasses import Topology
from ..utils.transpilation_utils import (
    build_calibration_maps,
    calculate_circuit_metrics
)

PI = math.pi


def calibration_aware_transpiler(
    qc: QuantumCircuit,
    topology: Topology,
    max_swaps_per_gate: int = 10,
    error_weight_gate: float = 0.4,
    error_weight_readout: float = 0.3,
    error_weight_decoherence: float = 0.3,
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:
    """
    Error-minimizing transpiler: finds optimal embedding and routes with error awareness.
    
    Args:
        qc: Normalized quantum circuit
        topology: Target topology with calibration data
        max_swaps_per_gate: Max SWAPs to route a gate
        error_weight_gate: Weight for gate errors (0-1)
        error_weight_readout: Weight for readout errors (0-1)
        error_weight_decoherence: Weight for decoherence errors (0-1)
    
    Returns:
        (transpiled_circuit, embedding, metrics)
    """
    print(f"[EMT] Starting Error-Minimizing Transpilation")
    print(f"[EMT] Circuit: {qc.num_qubits} logical qubits, {len(qc.operations)} operations")
    print(f"[EMT] Topology: {topology.numQubits} physical qubits")

    coupling_set = build_coupling_set(topology.coupling_map)
    adjacency = _build_adjacency_list(topology.coupling_map)
    print(f"[EMT] Building distance matrix...")
    gate_error_map, gate_duration_map = build_calibration_maps(topology)
    distance_matrix = _build_distance_matrix(adjacency, topology.numQubits)
    print(f"[EMT] Distance matrix built")

    # Normalize error weights
    total_weight = error_weight_gate + error_weight_readout + error_weight_decoherence
    w_gate = error_weight_gate / total_weight
    w_readout = error_weight_readout / total_weight
    w_decoherence = error_weight_decoherence / total_weight

    # Find initial embedding
    print(f"[EMT] Finding initial embedding...")
    embedding = _find_embedding(qc, topology, adjacency, w_gate, w_readout, w_decoherence)
    print(f"[EMT] Initial embedding: {embedding}")
    
    # Check if embedding respects topology connectivity
    print(f"[EMT] Validating embedding against topology connectivity...")
    invalid_gates = []
    for op in qc.operations:
        if isinstance(op, Operation) and len(op.qubits) == 2:
            l0, l1 = op.qubits
            p0, p1 = embedding[l0], embedding[l1]
            # Check if physical qubits are adjacent
            if not ((p0, p1) in coupling_set or (p1, p0) in coupling_set):
                invalid_gates.append((op.name, l0, l1, p0, p1))
    
    if invalid_gates:
        print(f"[EMT] ⚠️  Found {len(invalid_gates)} two-qubit gates that need routing:")
        for name, l0, l1, p0, p1 in invalid_gates[:5]:  # Show first 5
            d = distance_matrix.get((p0, p1), 999)
            print(f"     {name} q[{l0}], q[{l1}] → physical ({p0}, {p1}), distance={d}")
    else:
        print(f"[EMT] ✅ All two-qubit gates respect topology connectivity!")

    # Route circuit
    # Note: Keep using logical qubits (4) for memory efficiency
    # Physical qubit mapping is stored in the embedding
    print(f"[EMT] Starting routing phase...")
    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    operations = list(qc.operations)
    dependencies = _build_dependencies(operations)
    executed = [False] * len(operations)
    swaps_per_gate = defaultdict(int)
    logical_swap_count = 0
    routing_gate_count = 0
    iteration = 0

    while not all(executed):
        iteration += 1
        if iteration > 1000:
            print(f"[EMT] Max iterations (1000) reached, breaking")
            break

        front_layer = _get_front_layer(executed, dependencies)
        if not front_layer:
            print(f"[EMT] No front layer found at iteration {iteration}")
            break

        progress = False

        # Try to execute gates
        for idx in front_layer:
            if executed[idx]:
                continue

            op = operations[idx]

            if not isinstance(op, Operation):
                transpiled_qc.operations.append(op)
                executed[idx] = True
                progress = True
                continue

            # Single-qubit gates
            if len(op.qubits) == 1:
                q0 = op.qubits[0]
                p0 = embedding[q0]

                phys_op = Operation(
                    name=op.name,
                    qubits=[p0],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata,
                )
                transpiled_qc.operations.append(phys_op)
                executed[idx] = True
                progress = True
                continue

            # Two-qubit gates
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]

            if (p0, p1) in coupling_set or (p1, p0) in coupling_set:
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0, p1],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata,
                )
                transpiled_qc.operations.append(phys_op)
                executed[idx] = True
                progress = True
                continue

            # Not adjacent: needs SWAPs
            swaps_per_gate[idx] += 1
            if swaps_per_gate[idx] > max_swaps_per_gate:
                print(f"[EMT] Gate {idx} exceeded max SWAPs ({max_swaps_per_gate}), forcing execution")
                phys_op = Operation(
                    name=op.name,
                    qubits=[p0, p1],
                    params=op.params,
                    clbits=op.clbits,
                    condition=op.condition,
                    metadata=op.metadata,
                )
                transpiled_qc.operations.append(phys_op)
                executed[idx] = True
                progress = True

        if progress:
            continue

        # Insert SWAP
        print(f"[EMT] No progress at iteration {iteration}, selecting best SWAP...")
        best_swap = _select_best_swap(
            executed, operations, dependencies, embedding, adjacency, distance_matrix, gate_error_map, front_layer
        )

        if best_swap is None:
            print(f"[EMT] No valid SWAP found, breaking")
            break

        swap_q0, swap_q1 = best_swap
        print(f"[EMT] Iteration {iteration}: SWAP({swap_q0}, {swap_q1}) @ physical ({embedding[swap_q0]}, {embedding[swap_q1]})")

        # Decompose SWAP
        p0, p1 = embedding[swap_q0], embedding[swap_q1]
        cx_pairs = [(p0, p1), (p1, p0), (p0, p1)]
        for control, target in cx_pairs:
            transpiled_qc.operations.append(Operation("cx", qubits=[control, target]))
            routing_gate_count += 1

        logical_swap_count += 1
        embedding[swap_q0], embedding[swap_q1] = embedding[swap_q1], embedding[swap_q0]

    # Add remaining unexecuted operations
    print(f"[EMT] Finalizing circuit...")
    unexecuted_count = sum(1 for done in executed if not done)
    if unexecuted_count > 0:
        print(f"[EMT] Warning: {unexecuted_count} unexecuted operations added as-is")
    
    for i, done in enumerate(executed):
        if not done:
            transpiled_qc.operations.append(operations[i])
    
    # Convert physical qubits back to logical for storage
    print(f"[EMT] Converting physical qubits back to logical...")
    physical_to_logical = {p: l for l, p in embedding.items()}
    
    converted_ops = []
    for op in transpiled_qc.operations:
        try:
            # Convert qubits from physical to logical
            if op.qubits and all(q in physical_to_logical for q in op.qubits):
                logical_qubits = [physical_to_logical[q] for q in op.qubits]
                converted_op = Operation(
                    name=op.name,
                    qubits=logical_qubits,
                    clbits=op.clbits,
                    params=op.params,
                    condition=op.condition,
                    metadata=op.metadata,
                )
                converted_ops.append(converted_op)
            else:
                # Operation with no qubits or invalid physical qubits, keep as-is
                converted_ops.append(op)
        except Exception as e:
            print(f"[EMT] Warning: could not convert operation {op}: {e}")
            converted_ops.append(op)
    
    transpiled_qc.operations = converted_ops

    print(f"[EMT] Calculating depth...")
    try:
        transpiled_qc.depth = transpiled_qc.calculate_depth() if hasattr(transpiled_qc, 'calculate_depth') else len(transpiled_qc.operations)
    except Exception as e:
        print(f"[EMT] Error calculating depth: {e}")
        transpiled_qc.depth = len(transpiled_qc.operations)

    print(f"[EMT] Calculating metrics...")
    try:
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
    except Exception as e:
        print(f"[EMT] Error calculating metrics: {e}")
        metrics = {
            "routing_gate_count": routing_gate_count,
            "total_physical_gates": len(transpiled_qc.operations),
            "iterations": iteration,
            "fidelity": 0.0,
        }

    print(f"[EMT] Transpilation finished")
    print(f"[EMT] Logical SWAPs: {logical_swap_count}")
    print(f"[EMT] Routing gates: {routing_gate_count}")
    print(f"[EMT] Total physical gates: {len(transpiled_qc.operations)}")
    print(f"[EMT] Circuit depth: {transpiled_qc.depth}")
    if "fidelity" in metrics:
        print(f"[EMT] Total fidelity: {metrics['fidelity']:.6f}")

    return transpiled_qc, embedding, metrics


def build_coupling_set(coupling_map):
    """Build set of valid (control, target) pairs"""
    return set(tuple(pair) if isinstance(pair, list) else pair for pair in coupling_map)


def _build_adjacency_list(coupling_map):
    """Build undirected adjacency list"""
    adj = defaultdict(set)
    for u, v in coupling_map:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _build_distance_matrix(adjacency, num_qubits):
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
    """Build dependency graph"""
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
    """Get ready-to-execute operations"""
    front_layer = []
    for i in range(len(executed)):
        if not executed[i] and all(executed[dep] for dep in dependencies[i]):
            front_layer.append(i)
    return front_layer


def _find_embedding(qc, topology, adjacency, w_gate, w_readout, w_decoherence):
    """
    Find initial embedding considering both qubit quality AND connectivity.
    
    Strategy: For small circuits (4 qubits), find a cluster of nearby good qubits.
    """
    num_logical = qc.num_qubits
    
    # Score physical qubits by quality
    physical_quality = {}
    for p_q in range(topology.numQubits):
        readout_err = 0.0
        t2 = float("inf")
        
        if topology.calibrationData:
            for q_cal in topology.calibrationData.qubits:
                if q_cal.qubit == p_q:
                    if q_cal.readout_error:
                        readout_err = q_cal.readout_error
                    if q_cal.t2:
                        t2 = q_cal.t2
                    break
        
        # Score: prefer low readout error, high T2
        readout_quality = 1.0 / (1.0 + readout_err)
        coherence_quality = 1.0 if t2 == float("inf") else min(t2 / 100e-6, 1.0)
        
        quality = (w_readout * readout_quality + w_decoherence * coherence_quality)
        physical_quality[p_q] = quality
    
    # For small circuits, find a connected cluster of good qubits
    best_embedding = None
    best_cluster_quality = -float("inf")
    
    # Try starting from each physical qubit
    for start_qubit in range(topology.numQubits):
        # BFS to find nearest neighbors
        embedding_candidate = {0: start_qubit}  # Start with logical 0 at start_qubit
        visited_physical = {start_qubit}
        
        # Assign remaining logical qubits to nearby physical qubits
        for log_q in range(1, num_logical):
            # Find best unvisited neighbor of already-assigned qubits
            best_neighbor = None
            best_neighbor_quality = -float("inf")
            
            for assigned_log_q in range(log_q):
                assigned_phys_q = embedding_candidate[assigned_log_q]
                # Look at neighbors of this physical qubit
                for neighbor_phys in adjacency.get(assigned_phys_q, []):
                    if neighbor_phys not in visited_physical:
                        neighbor_quality = physical_quality.get(neighbor_phys, 0.0)
                        if neighbor_quality > best_neighbor_quality:
                            best_neighbor_quality = neighbor_quality
                            best_neighbor = neighbor_phys
            
            if best_neighbor is None:
                # No nearby neighbor found, break and try different start
                break
            
            embedding_candidate[log_q] = best_neighbor
            visited_physical.add(best_neighbor)
        
        # Check if we assigned all logical qubits
        if len(embedding_candidate) == num_logical:
            # Calculate cluster quality (sum of physical qubit qualities)
            cluster_quality = sum(physical_quality.get(embedding_candidate[lq], 0.0) 
                                 for lq in range(num_logical))
            
            if cluster_quality > best_cluster_quality:
                best_cluster_quality = cluster_quality
                best_embedding = embedding_candidate.copy()
    
    # If cluster-based approach failed, fall back to greedy
    if best_embedding is None:
        print(f"[EMT]   Cluster embedding failed, falling back to greedy")
        sorted_physical = sorted(range(topology.numQubits), 
                               key=lambda q: -physical_quality.get(q, 0.0))
        best_embedding = {i: sorted_physical[i] for i in range(num_logical)}
    
    return best_embedding


def _select_best_swap(executed, operations, dependencies, embedding, adjacency, distance_matrix, gate_error_map, front_layer):
    """Select best SWAP using error-aware heuristic"""
    blocked_gates = []
    
    # Find blocked gates
    for idx in front_layer:
        op = operations[idx]
        if isinstance(op, Operation) and len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]
            # Check if adjacent in either direction
            if not ((p0 in adjacency and p1 in adjacency[p0]) or (p1 in adjacency and p0 in adjacency[p1])):
                blocked_gates.append((idx, q0, q1))
    
    if not blocked_gates:
        return None
    
    # Score potential SWAPs - only consider swaps between adjacent physical qubits
    best_score = -float("inf")
    best_swap = None
    
    # Get all possible physical swaps (between adjacent qubits)
    possible_physical_swaps = set()
    for p_q in adjacency:
        for p_neighbor in adjacency[p_q]:
            if p_q < p_neighbor:
                possible_physical_swaps.add((p_q, p_neighbor))
    
    # Map back to logical qubits
    physical_to_logical = {p: l for l, p in embedding.items()}
    
    # Try all possible swaps
    for p0, p1 in possible_physical_swaps:
        # Find which logical qubits are at these physical locations
        if p0 not in physical_to_logical or p1 not in physical_to_logical:
            continue
        
        try:
            swap_q0 = physical_to_logical[p0]
            swap_q1 = physical_to_logical[p1]
        except KeyError:
            continue
        
        # Simulate swap
        temp_embedding = embedding.copy()
        temp_embedding[swap_q0], temp_embedding[swap_q1] = temp_embedding[swap_q1], temp_embedding[swap_q0]
        
        # Check if helps and compute score
        helps = False
        dist_improvement = 0
        
        for gate_idx, q0, q1 in blocked_gates:
            new_p0 = temp_embedding[q0]
            new_p1 = temp_embedding[q1]
            
            # Check if now adjacent
            if (new_p0 in adjacency and new_p1 in adjacency[new_p0]) or (new_p1 in adjacency and new_p0 in adjacency[new_p1]):
                helps = True
                break
            
            # Measure distance improvement
            old_dist = distance_matrix.get((embedding[q0], embedding[q1]), 999)
            new_dist = distance_matrix.get((new_p0, new_p1), 999)
            dist_improvement += old_dist - new_dist
        
        if not helps and dist_improvement <= 0:
            continue
        
        # Compute swap error cost
        cx_error = gate_error_map.get(("cx", tuple(sorted([p0, p1]))), 0.01)
        swap_error = 3 * cx_error  # 3 CX gates in SWAP decomposition
        
        score = dist_improvement - 10 * swap_error
        if helps:
            score += 100
        
        if score > best_score:
            best_score = score
            best_swap = (swap_q0, swap_q1)
    
    # Fallback: if no SWAP helps, pick one that improves distance the most
    if best_swap is None:
        print(f"[EMT]   No SWAP directly helps, trying distance-improvement heuristic...")
        best_score = -float("inf")
        
        for p0, p1 in possible_physical_swaps:
            if p0 not in physical_to_logical or p1 not in physical_to_logical:
                continue
            
            try:
                swap_q0 = physical_to_logical[p0]
                swap_q1 = physical_to_logical[p1]
            except KeyError:
                continue
            
            # Simulate swap
            temp_embedding = embedding.copy()
            temp_embedding[swap_q0], temp_embedding[swap_q1] = temp_embedding[swap_q1], temp_embedding[swap_q0]
            
            # Score based on total distance improvement to all blocked gates
            total_dist_improvement = 0
            for gate_idx, q0, q1 in blocked_gates:
                old_dist = distance_matrix.get((embedding[q0], embedding[q1]), 999)
                new_dist = distance_matrix.get((temp_embedding[q0], temp_embedding[q1]), 999)
                total_dist_improvement += old_dist - new_dist
            
            if total_dist_improvement > best_score:
                best_score = total_dist_improvement
                best_swap = (swap_q0, swap_q1)
        
        if best_swap:
            print(f"[EMT]   Found SWAP with distance improvement {best_score}")
    
    return best_swap