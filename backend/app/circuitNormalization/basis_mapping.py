from ..core.QuantumCircuit import QuantumCircuit, Operation
import math

PI = math.pi
CONTROL_FLOW_OPS = {"measure", "barrier", "for_loop", "while_loop", "if_else"}

def _copy(op, name=None, qubits=None, params=None):
    """Copy an operation with optional overrides for name, qubits, params"""
    return Operation(
        name=name or op.name,
        qubits=qubits or op.qubits,
        params=params if params is not None else op.params,
        clbits=list(op.clbits),
        condition=op.condition,
        metadata=dict(op.metadata),
    )

def map_to_basis(circuit: QuantumCircuit, target_basis: list) -> QuantumCircuit:
    """
    Map canonical/internal IR gates to an arbitrary target basis, preserving per-qubit timeline.
    """
    target_basis = {g.lower() for g in target_basis}
    new_circuit = QuantumCircuit(
        num_qubits=circuit.num_qubits,
        num_clbits=circuit.num_clbits,
        metadata=dict(circuit.metadata),
    )

    # Track the logical time step of the last operation on each qubit
    last_time = [-1] * circuit.num_qubits
    
    for idx, op in enumerate(circuit.operations):
        name = op.name.lower()
        qubits = op.qubits
        params = op.params

        # Control flow passthrough
        if name in CONTROL_FLOW_OPS:
            new_circuit.add_operation(op)
            # Use the original circuit index as the logical time
            for q in qubits:
                last_time[q] = idx
            continue

        # Determine the logical time for this operation
        # It must come after all operations on its qubits
        current_time = max((last_time[q] for q in qubits), default=-1) + 1

        # Prepare list of operations to insert
        ops_to_add = []

        # ---------- Single-qubit gates ----------
        if name in {"x", "y", "z"}:
            theta = PI
            if name in target_basis:
                ops_to_add.append(_copy(op))
            elif name == "x" and {"rx", "rz"} <= target_basis:
                ops_to_add.append(_copy(op, "rx", params=[theta]))
            elif name == "y" and {"rx", "rz"} <= target_basis:
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "rx", params=[theta]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            elif {"sx", "rz"} <= target_basis:
                if name in {"x", "y"}:
                    ops_to_add.extend([
                        _copy(op, "rz", params=[-PI/2]),
                        _copy(op, "sx", params=[]),
                        _copy(op, "rz", params=[theta]),
                        _copy(op, "sx", params=[]),
                        _copy(op, "rz", params=[PI/2]),
                    ])
                elif name == "z":
                    ops_to_add.append(_copy(op, "rz", params=[theta]))
            else:
                raise NotImplementedError(f"Cannot map {name.upper()} to target basis {target_basis}")

        # ---------- RX/RY/RZ ----------
        elif name in {"rx", "ry", "rz"}:
            theta = params[0] if params else None
            if name in target_basis:
                ops_to_add.append(_copy(op))
            elif name == "rx" and {"sx", "rz"} <= target_basis:
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[theta]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            elif name == "ry" and {"rx", "rz"} <= target_basis:
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "rx", params=[theta]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            elif name == "ry" and {"sx", "rz"} <= target_basis:
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[theta]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            elif name == "rz" and "rz" in target_basis:
                ops_to_add.append(_copy(op))
            else:
                raise NotImplementedError(f"Cannot map {name.upper()} to target basis {target_basis}")

        # ---------- H/S/T ----------
        elif name in {"h", "s", "t"}:
            if name in target_basis:
                ops_to_add.append(_copy(op))
            elif {"rx", "rz"} <= target_basis:
                if name == "h":
                    ops_to_add.extend([
                        _copy(op, "rz", params=[PI]),
                        _copy(op, "rx", params=[PI/2]),
                        _copy(op, "rz", params=[PI]),
                    ])
                elif name == "s":
                    ops_to_add.append(_copy(op, "rz", params=[PI/2]))
                elif name == "t":
                    ops_to_add.append(_copy(op, "rz", params=[PI/4]))
            elif {"sx", "rz"} <= target_basis:
                if name == "h":
                    ops_to_add.extend([
                        _copy(op, "rz", params=[PI]),
                        _copy(op, "sx", params=[]),
                        _copy(op, "rz", params=[PI/2]),
                    ])
                elif name == "s":
                    ops_to_add.append(_copy(op, "rz", params=[PI/2]))
                elif name == "t":
                    ops_to_add.append(_copy(op, "rz", params=[PI/4]))
            else:
                raise NotImplementedError(f"Cannot map {name.upper()} to target basis {target_basis}")

        # ---------- Two-qubit gates ----------
        elif name == "cx":
            c, t = qubits
            if "cx" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"cz", "sx", "rz"} <= target_basis:
                ops_to_add.extend([
                    _copy(op, "rz", qubits=[t], params=[PI]),
                    _copy(op, "sx", qubits=[t], params=[]),
                    _copy(op, "rz", qubits=[t], params=[PI/2]),
                    _copy(op, "cz", qubits=[c, t], params=[]),
                    _copy(op, "rz", qubits=[t], params=[PI]),
                    _copy(op, "sx", qubits=[t], params=[]),
                    _copy(op, "rz", qubits=[t], params=[PI/2]),
                ])
            else:
                raise NotImplementedError(f"Cannot map CX to target basis {target_basis}")

        elif name == "cz":
            if "cz" in target_basis:
                ops_to_add.append(_copy(op))
            else:
                raise NotImplementedError(f"Cannot map CZ to target basis {target_basis}")

        elif name == "swap":
            q0, q1 = qubits
            if "swap" in target_basis:
                ops_to_add.append(_copy(op))
            elif "cx" in target_basis:
                ops_to_add.extend([
                    _copy(op, "cx", [q0, q1], []),
                    _copy(op, "cx", [q1, q0], []),
                    _copy(op, "cx", [q0, q1], []),
                ])
            else:
                raise NotImplementedError(f"Cannot map SWAP to target basis {target_basis}")

        elif name in target_basis:
            ops_to_add.append(_copy(op))

        else:
            raise NotImplementedError(f"Unsupported gate {op.name} for target basis {target_basis}")

        # Add all decomposed operations and update timeline
        for new_op in ops_to_add:
            new_circuit.add_operation(new_op)
            # Update the logical time for all qubits involved in this operation
            for q in new_op.qubits:
                last_time[q] = current_time
    new_circuit.depth = new_circuit.calculate_depth()
    print(f"[DEBUG] Finished mapping. New circuit has {len(new_circuit.operations)} operations")
    return new_circuit