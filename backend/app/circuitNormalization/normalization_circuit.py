from ..core.QuantumCircuit import QuantumCircuit
from . import normalization_operation  # import the module
CONTROL_FLOW_OPS = {"measure", "barrier", "for_loop", "while_loop", "if_else"}

def normalize_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    print(f"[DEBUG] Starting normalization for circuit with {circuit.num_qubits} qubits and {len(circuit.operations)} operations")

    new_circuit = QuantumCircuit(
        num_qubits=circuit.num_qubits,
        num_clbits=circuit.num_clbits,
        metadata=dict(circuit.metadata),
    )

    for idx, op in enumerate(circuit.operations):
        print(f"[DEBUG] Operation {idx}: {op.name} on qubits {op.qubits} with params {op.params}")

        # Leave control flow untouched
        if op.name in CONTROL_FLOW_OPS:
            print(f"[DEBUG] Skipping control-flow op: {op.name}")
            new_circuit.add_operation(op)
            continue

        try:
            print(f"[DEBUG] Calling normalization_operation.normalize_operation_recursive for {op.name}")
            lowered_ops = normalization_operation.normalize_operation_recursive(op)
            print(f"[DEBUG] Result of normalization: {len(lowered_ops)} operations")
        except Exception as e:
            print(f"[ERROR] Failed to normalize operation {op.name}: {e}")
            raise

        for lop_idx, lop in enumerate(lowered_ops):
            print(f"[DEBUG] Adding lowered operation {lop_idx}: {lop.name} on qubits {lop.qubits} with params {lop.params}")
            new_circuit.add_operation(lop)

    print(f"[DEBUG] Finished normalization. Total operations in new circuit: {len(new_circuit.operations)}")
    return new_circuit
