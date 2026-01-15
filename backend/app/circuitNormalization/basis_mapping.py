from ..core.QuantumCircuit import QuantumCircuit, Operation
import math

CONTROL_FLOW_OPS = {"measure", "barrier", "for_loop", "while_loop", "if_else"}
PI = math.pi

def map_to_basis(circuit: QuantumCircuit, target_basis: list) -> QuantumCircuit:
    """
    Map canonical IR (rx, rz, cx) to an arbitrary target basis.
    
    Args:
        circuit: QuantumCircuit in canonical basis
        target_basis: list of supported gate names (e.g., ['rz', 'sx', 'cx'])
        
    Returns:
        QuantumCircuit mapped to the target basis
    """
    new_circuit = QuantumCircuit(
        num_qubits=circuit.num_qubits,
        num_clbits=circuit.num_clbits,
        metadata=dict(circuit.metadata),
    )

    for op in circuit.operations:
        # leave control flow untouched
        if op.name in CONTROL_FLOW_OPS:
            new_circuit.add_operation(op)
            continue

        # Single-qubit gate mapping
        if op.name == "rx":
            theta = op.params[0]
            if "rx" in target_basis:
                new_circuit.add_operation(Operation("rx", op.qubits, params=[theta], metadata=op.metadata))
            elif "sx" in target_basis:
                # decompose rx(theta) into sx + rz if needed
                # RX(theta) = RZ(-pi/2) SX RZ(theta) SX RZ(pi/2)
                new_circuit.add_operation(Operation("rz", op.qubits, params=[-PI/2], metadata=op.metadata))
                new_circuit.add_operation(Operation("sx", op.qubits, metadata=op.metadata))
                new_circuit.add_operation(Operation("rz", op.qubits, params=[theta], metadata=op.metadata))
                new_circuit.add_operation(Operation("sx", op.qubits, metadata=op.metadata))
                new_circuit.add_operation(Operation("rz", op.qubits, params=[PI/2], metadata=op.metadata))
            else:
                raise NotImplementedError(f"No rule to map RX to target basis {target_basis}")

        elif op.name == "rz":
            theta = op.params[0]
            if "rz" in target_basis:
                new_circuit.add_operation(Operation("rz", op.qubits, params=[theta], metadata=op.metadata))
            else:
                raise NotImplementedError(f"No rule to map RZ to target basis {target_basis}")

        # Two-qubit gate mapping
        elif op.name == "cx":
            q0, q1 = op.qubits
            if "cx" in target_basis:
                new_circuit.add_operation(Operation("cx", [q0, q1], metadata=op.metadata))
            elif "cz" in target_basis and "sx" in target_basis:
                # CX → H(target) CZ(control,target) H(target)
                # Since H = RZ(pi) RX(pi/2) RZ(pi) in canonical → approximate with SX + RZ
                new_circuit.add_operation(Operation("rz", [q1], params=[PI], metadata=op.metadata))
                new_circuit.add_operation(Operation("sx", [q1], metadata=op.metadata))
                new_circuit.add_operation(Operation("rz", [q1], params=[PI/2], metadata=op.metadata))
                new_circuit.add_operation(Operation("cz", [q0, q1], metadata=op.metadata))
                new_circuit.add_operation(Operation("rz", [q1], params=[PI], metadata=op.metadata))
                new_circuit.add_operation(Operation("sx", [q1], metadata=op.metadata))
                new_circuit.add_operation(Operation("rz", [q1], params=[PI/2], metadata=op.metadata))
            else:
                raise NotImplementedError(f"No rule to map CX to target basis {target_basis}")

        # Already mapped or unsupported
        else:
            if op.name in target_basis:
                new_circuit.add_operation(op)
            else:
                raise NotImplementedError(f"Unsupported gate {op.name} for target basis {target_basis}")

    return new_circuit
