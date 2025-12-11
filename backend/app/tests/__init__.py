import json
import random
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit

# Generate a random circuit
num_qubits = random.randint(3, 6)  # Random number of qubits between 3 and 6
depth = random.randint(10, 30)  # Random depth between 10 and 30

qc = random_circuit(num_qubits, depth, measure=False, seed=42)

# Convert to custom JSON format (matching your structure)
def circuit_to_custom_json(circuit):
    gates_list = []
    
    for instruction, qargs, cargs in circuit.data:
        gate_dict = {
            "name": instruction.name,
            "qubits": [circuit.qubits.index(q) for q in qargs],
            "params": [float(p) for p in instruction.params]
        }
        gates_list.append(gate_dict)
    
    return {
        "num_qubits": circuit.num_qubits,
        "gates": gates_list
    }

# Convert and save
circuit_json = circuit_to_custom_json(qc)

with open('random_circuit.json', 'w') as f:
    json.dump(circuit_json, f, indent=2)

print(f"Generated random circuit with {num_qubits} qubits and {len(circuit_json['gates'])} gates")
print(f"Saved to random_circuit.json")

# Also print the circuit
print("\nCircuit preview:")
print(qc)