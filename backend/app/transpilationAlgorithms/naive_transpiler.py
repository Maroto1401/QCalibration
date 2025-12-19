from typing import Dict, Tuple
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


def naive_transpiler(
    qc: QuantumCircuit,
    topology
) -> Tuple[QuantumCircuit, Dict[int, int], Dict[str, float]]:

    embedding = {i: i for i in range(qc.num_qubits)}

    coupling_set = build_coupling_set(topology.coupling_map)
    gate_error_map, gate_duration_map = build_calibration_maps(topology)

    transpiled_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)

    gates_inserted = 0
    total_gate_error = 0.0
    total_duration = 0.0

    for op in qc.operations:

        if not isinstance(op, Operation):
            transpiled_qc.operations.append(op)
            continue

        # === SINGLE-QUBIT ===
        if len(op.qubits) == 1:
            transpiled_qc.operations.append(op)
            error, duration = track_single_qubit_gate(
                op, embedding, gate_error_map, gate_duration_map
            )
            total_gate_error += error
            total_duration += duration

        # === TWO-QUBIT ===
        elif len(op.qubits) == 2:
            q0, q1 = op.qubits
            p0, p1 = embedding[q0], embedding[q1]

            if is_connected(p0, p1, coupling_set):
                transpiled_qc.operations.append(op)
                error, duration = track_two_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration

            else:
                # INSERT SWAP
                swap_op = Operation(name="swap", qubits=[q0, q1])
                transpiled_qc.operations.append(swap_op)
                gates_inserted += 1

                swap_error = estimate_swap_error(p0, p1, gate_error_map)
                cx_duration = get_gate_duration(
                    "cx", [p0, p1], gate_duration_map
                )

                total_gate_error += swap_error
                total_duration += 3 * cx_duration

                # Update embedding
                embedding[q0], embedding[q1] = embedding[q1], embedding[q0]

                # Apply original gate
                transpiled_qc.operations.append(op)
                error, duration = track_two_qubit_gate(
                    op, embedding, gate_error_map, gate_duration_map
                )
                total_gate_error += error
                total_duration += duration

        # === >2-QUBIT (NOT SUPPORTED) ===
        else:
            raise NotImplementedError(
                f"Multi-qubit gate '{op.name}' with {len(op.qubits)} qubits is not supported."
            )

    metrics = calculate_circuit_metrics(
        original_qc=qc,
        transpiled_qc=transpiled_qc,
        gates_inserted=gates_inserted,
        total_gate_error=total_gate_error,
        total_duration=total_duration,
        embedding=embedding,
        topology=topology,
    )

    return transpiled_qc, embedding, metrics
