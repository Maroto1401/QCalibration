# check_logical_vs_normalized.py
import os
import sys
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import numpy as np

# -------------------- CONFIG --------------------
# Folder containing your QASM2 files
CIRCUITS_FOLDER = "circuits"
LOGICAL_QASM = "logical_circuit.qasm"
NORMALIZED_QASM = "normalized_naive.qasm"
# ------------------------------------------------

def load_circuit(path):
    """Load a QuantumCircuit from QASM2 file."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    return QuantumCircuit.from_qasm_file(path)

def main():
    logical_path = os.path.join(CIRCUITS_FOLDER, LOGICAL_QASM)
    normalized_path = os.path.join(CIRCUITS_FOLDER, NORMALIZED_QASM)

    logical_circ = load_circuit(logical_path)
    normalized_circ = load_circuit(normalized_path)

    print(f"Logical circuit qubits: {logical_circ.num_qubits}")
    print(f"Normalized circuit qubits: {normalized_circ.num_qubits}")

    if logical_circ.num_qubits != normalized_circ.num_qubits:
        print("Error: Number of qubits does not match.")
        sys.exit(1)

    # Compute unitaries
    U_logical = Operator(logical_circ).data
    U_normalized = Operator(normalized_circ).data

    # Check equivalence
    if np.allclose(U_logical, U_normalized, atol=1e-10):
        print("✅ Logical and normalized circuits are UNITARY-equivalent.")
    else:
        print("❌ Circuits are NOT equivalent!")
        diff = np.max(np.abs(U_logical - U_normalized))
        print(f"Max element-wise difference: {diff:e}")

if __name__ == "__main__":
    main()
