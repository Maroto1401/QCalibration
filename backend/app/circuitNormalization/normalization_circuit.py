
from .normalization_operation import normalize_operation_recursive
from ..core import QuantumCircuit

CONTROL_FLOW_OPS = {"measure", "barrier", "for_loop", "while_loop", "if_else"}

def normalize_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    new_circuit = QuantumCircuit(
        num_qubits=circuit.num_qubits,
        num_clbits=circuit.num_clbits,
        metadata=dict(circuit.metadata),
    )

    for op in circuit.operations:
        # Leave control flow untouched 
        if op.name in CONTROL_FLOW_OPS:
            new_circuit.add_operation(op)
            continue

        lowered_ops = normalize_operation_recursive(op)
        for lop in lowered_ops:
            new_circuit.add_operation(lop)

    return new_circuit

