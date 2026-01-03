import random
from qiskit.circuit.random import random_circuit
from qiskit.qasm2 import dumps

# Generate random circuit
num_qubits = random.randint(10, 30)
depth = random.randint(10, 30)

qc = random_circuit(
    num_qubits,
    depth,
    measure=False,
    max_operands=2,
    seed=42
)

# Export to OpenQASM 2.0
qasm_str = dumps(qc)

with open("random_circuit.qasm", "w") as f:
    f.write(qasm_str)

print(f"Saved OpenQASM 2.0 circuit with {num_qubits} qubits")
print(qc)
