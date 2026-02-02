# check_logical_vs_normalized_no_aer.py
import os
import sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

# -------------------- CONFIG --------------------
CIRCUITS_FOLDER = "circuits"
LOGICAL_QASM = "logical_circuit.qasm"
NORMALIZED_QASM = "normalized_naive.qasm"
# ------------------------------------------------

def load_circuit(path):
    """Load a QuantumCircuit from a QASM2 file."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    return QuantumCircuit.from_qasm_file(path)

def check_unitary_equivalence(circ1, circ2, atol=1e-10):
    """Check if two circuits are unitarily equivalent."""
    U1 = Operator(circ1).data
    U2 = Operator(circ2).data
    if np.allclose(U1, U2, atol=atol):
        print("✅ Circuits are UNITARY-equivalent.")
        return True
    else:
        print("❌ Circuits are NOT unitarily equivalent!")
        diff = np.max(np.abs(U1 - U2))
        print(f"Max element-wise difference: {diff:e}")
        return False

def check_statevector_equivalence(circ1, circ2, atol=1e-10):
    """Check if two circuits produce the same quantum state."""
    # Simulate the circuits using Statevector
    sv1 = Statevector.from_instruction(circ1)
    sv2 = Statevector.from_instruction(circ2)
    
    # Calculate fidelity
    fidelity = np.abs(sv1.inner(sv2))
    
    if np.abs(fidelity - 1.0) < atol:
        print(f"✅ Statevector check passed (fidelity: {fidelity:.15f})")
        return True
    else:
        print(f"❌ Statevector check FAILED (fidelity: {fidelity:.15f})")
        return False

def check_probability_equivalence(circ1, circ2, atol=1e-10):
    """Check if measurement probabilities are the same."""
    sv1 = Statevector.from_instruction(circ1)
    sv2 = Statevector.from_instruction(circ2)
    
    prob1 = np.abs(sv1.data) ** 2
    prob2 = np.abs(sv2.data) ** 2
    
    if np.allclose(prob1, prob2, atol=atol):
        print("✅ Probability check passed.")
        return True
    else:
        print("❌ Probability check FAILED.")
        diff = np.max(np.abs(prob1 - prob2))
        print(f"Max probability difference: {diff:e}")
        return False

def main():
    logical_path = os.path.join(CIRCUITS_FOLDER, LOGICAL_QASM)
    normalized_path = os.path.join(CIRCUITS_FOLDER, NORMALIZED_QASM)

    logical_circ = load_circuit(logical_path)
    normalized_circ = load_circuit(normalized_path)

    print("=" * 60)
    print(f"Logical circuit: {LOGICAL_QASM}")
    print(f"  Qubits: {logical_circ.num_qubits}")
    print(f"  Gates: {logical_circ.size()}")
    
    print(f"\nNormalized circuit: {NORMALIZED_QASM}")
    print(f"  Qubits: {normalized_circ.num_qubits}")
    print(f"  Gates: {normalized_circ.size()}")
    
    if logical_circ.num_qubits != normalized_circ.num_qubits:
        print("❌ Error: Number of qubits does not match!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("UNITARY EQUIVALENCE CHECK")
    print("-" * 60)
    unitary_ok = check_unitary_equivalence(logical_circ, normalized_circ)

    print("\n" + "=" * 60)
    print("STATEVECTOR EQUIVALENCE CHECK")
    print("-" * 60)
    statevector_ok = check_statevector_equivalence(logical_circ, normalized_circ)

    print("\n" + "=" * 60)
    print("PROBABILITY EQUIVALENCE CHECK")
    print("-" * 60)
    probability_ok = check_probability_equivalence(logical_circ, normalized_circ)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"Unitary equivalence: {'✅ PASS' if unitary_ok else '❌ FAIL'}")
    print(f"Statevector equivalence: {'✅ PASS' if statevector_ok else '❌ FAIL'}")
    print(f"Probability equivalence: {'✅ PASS' if probability_ok else '❌ FAIL'}")
    
    if statevector_ok and probability_ok:
        print("\n🎉 Circuits are physically equivalent!")
        if not unitary_ok:
            print("   Note: Circuits differ by a global phase")
    else:
        print("\n⚠️ Circuits are NOT equivalent!")

if __name__ == "__main__":
    main()