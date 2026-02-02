# check_normalized_vs_transpiled.py
import os
import sys
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import numpy as np

# -------------------- CONFIG --------------------
CIRCUITS_FOLDER = "circuits"
NORMALIZED_QASM = "normalized.qasm"
TRANSPILED_QASM = "transpiled.qasm"

# The final logical -> physical embedding after transpilation
# Example: {"0": 0, "1": 3, "2": 1, "3": 2}
EMBEDDING = {
    "0": 0,
    "1": 3,
    "2": 1,
    "3": 2,
}
# ------------------------------------------------

def load_circuit(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    return QuantumCircuit.from_qasm_file(path)

def reorder_qubits(circ, embedding):
    """
    Reorder qubits according to embedding (logical -> physical)
    so we can compare unitary matrices.
    """
    num_qubits = circ.num_qubits
    reorder = [0] * num_qubits
    for logical, physical in embedding.items():
        reorder[int(physical)] = int(logical)
    return circ.permute_qubits(reorder)

def main():
    normalized_path = os.path.join(CIRCUITS_FOLDER, NORMALIZED_QASM)
    transpiled_path = os.path.join(CIRCUITS_FOLDER, TRANSPILED_QASM)

    normalized_circ = load_circuit(normalized_path)
    transpiled_circ = load_circuit(transpiled_path)

    # Apply embedding permutation to transpiled circuit
    transpiled_circ = reorder_qubits(transpiled_circ, EMBEDDING)

    # Compute unitaries
    U_norm = Operator(normalized_circ).data
    U_transp = Operator(transpiled_circ).data

    # Check equivalence
    if np.allclose(U_norm, U_transp, atol=1e-10):
        print("✅ Normalized and transpiled circuits are UNITARY-equivalent (modulo swaps).")
    else:
        print("❌ Circuits are NOT equivalent!")
        diff = np.max(np.abs(U_norm - U_transp))
        print(f"Max element-wise difference: {diff:e}")

if __name__ == "__main__":
    main()
