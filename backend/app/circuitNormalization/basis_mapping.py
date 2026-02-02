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
    Map canonical/internal IR gates to an arbitrary target basis {cz, rz, sx, x, id}.
    
    VERIFIED DECOMPOSITIONS (basis: {cz, rz, sx, x, id}):
    - H = SX RZ(π/2) SX
    - X = SX SX
    - Z = RZ(π)
    - RX(θ) = SX RZ(π/2) SX RZ(θ) SX RZ(π/2) SX
    - RY(θ) = RZ(-π/2) RX(θ) RZ(π/2)
    - Y = RZ(-π/2) RX(π) RZ(π/2)
    - CX(c,t) = H[t] CZ(c,t) H[t] where H = SX RZ(π/2) SX
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
            for q in qubits:
                last_time[q] = idx
            continue

        # Determine the logical time for this operation
        current_time = max((last_time[q] for q in qubits), default=-1) + 1

        # Prepare list of operations to insert
        ops_to_add = []

        # ---------- Single-qubit gates ----------
        if name == "h":
            if "h" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"sx", "rz"} <= target_basis:
                # H = SX RZ(π/2) SX
                ops_to_add.extend([
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                ])
            else:
                raise NotImplementedError(f"Cannot map H to target basis {target_basis}")

        elif name == "x":
            if "x" in target_basis:
                ops_to_add.append(_copy(op))
            elif "sx" in target_basis:
                # X = SX SX
                ops_to_add.extend([
                    _copy(op, "sx", params=[]),
                    _copy(op, "sx", params=[]),
                ])
            else:
                raise NotImplementedError(f"Cannot map X to target basis {target_basis}")

        elif name == "z":
            if "z" in target_basis:
                ops_to_add.append(_copy(op))
            elif "rz" in target_basis:
                # Z = RZ(π)
                ops_to_add.append(_copy(op, "rz", params=[PI]))
            else:
                raise NotImplementedError(f"Cannot map Z to target basis {target_basis}")

        elif name == "y":
            if "y" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"sx", "rz"} <= target_basis:
                # Y = RZ(-π/2) RX(π) RZ(π/2)
                # RX(π) = SX RZ(π/2) SX RZ(π) SX RZ(π/2) SX
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            else:
                raise NotImplementedError(f"Cannot map Y to target basis {target_basis}")

        # ---------- RX/RY/RZ ----------
        elif name == "rx":
            if "rx" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"sx", "rz"} <= target_basis:
                theta = params[0] if params else None
                # RX(θ) = SX RZ(π/2) SX RZ(θ) SX RZ(π/2) SX
                ops_to_add.extend([
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[theta]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                ])
            else:
                raise NotImplementedError(f"Cannot map RX to target basis {target_basis}")

        elif name == "ry":
            if "ry" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"sx", "rz"} <= target_basis:
                theta = params[0] if params else None
                # RY(θ) = RZ(-π/2) RX(θ) RZ(π/2)
                # = RZ(-π/2) [SX RZ(π/2) SX RZ(θ) SX RZ(π/2) SX] RZ(π/2)
                ops_to_add.extend([
                    _copy(op, "rz", params=[-PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[theta]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                    _copy(op, "sx", params=[]),
                    _copy(op, "rz", params=[PI/2]),
                ])
            else:
                raise NotImplementedError(f"Cannot map RY to target basis {target_basis}")

        elif name == "rz":
            if "rz" in target_basis:
                ops_to_add.append(_copy(op))
            else:
                raise NotImplementedError(f"Cannot map RZ to target basis {target_basis}")

        # ---------- Two-qubit gates ----------
        elif name == "cx":
            c, t = qubits
            if "cx" in target_basis:
                ops_to_add.append(_copy(op))
            elif {"cz", "sx", "rz"} <= target_basis:
                # CX(c,t) = H[t] CZ(c,t) H[t]
                # where H = SX RZ(π/2) SX
                ops_to_add.extend([
                    # First H on target: SX RZ(π/2) SX
                    _copy(op, "sx", qubits=[t], params=[]),
                    _copy(op, "rz", qubits=[t], params=[PI/2]),
                    _copy(op, "sx", qubits=[t], params=[]),
                    # CZ
                    _copy(op, "cz", qubits=[c, t], params=[]),
                    # Second H on target: SX RZ(π/2) SX
                    _copy(op, "sx", qubits=[t], params=[]),
                    _copy(op, "rz", qubits=[t], params=[PI/2]),
                    _copy(op, "sx", qubits=[t], params=[]),
                ])
            else:
                raise NotImplementedError(f"Cannot map CX to target basis {target_basis}")

        elif name == "cz":
            if "cz" in target_basis:
                ops_to_add.append(_copy(op))
            else:
                raise NotImplementedError(f"Cannot map CZ to target basis {target_basis}")

        elif name == "swap":
            if "swap" in target_basis:
                ops_to_add.append(_copy(op))
            else:
                raise NotImplementedError(f"Cannot map SWAP to target basis {target_basis}")

        elif name in target_basis:
            ops_to_add.append(_copy(op))

        else:
            raise NotImplementedError(f"Unsupported gate {op.name} for target basis {target_basis}")

        # Add all decomposed operations and update timeline
        for new_op in ops_to_add:
            new_circuit.add_operation(new_op)
            # Each decomposed operation advances time on its qubits
            for q in new_op.qubits:
                last_time[q] += 1
    
    new_circuit.depth = new_circuit.calculate_depth()
    print(f"[DEBUG] Finished mapping. New circuit has {len(new_circuit.operations)} operations")
    return new_circuit