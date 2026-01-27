from qiskit import QuantumCircuit
import os

# Path to the QASM file
qasm_path = "output/random_circuit.qasm"

if not os.path.exists(qasm_path):
    raise FileNotFoundError(f"QASM file not found: {qasm_path}")

# Load the circuit from QASM
circuit = QuantumCircuit.from_qasm_file(qasm_path)

# Print basic info
print(f"Qubits: {circuit.num_qubits}")
print(f"Depth: {circuit.depth()}")
print()

# Text-based visualization
print(circuit.draw(output="text"))
