# check_normalized_vs_transpiled.py
import os
import sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

# -------------------- CONFIG --------------------
CIRCUITS_FOLDER = "circuits"
NORMALIZED_QASM = "normalized.qasm"
TRANSPILED_QASM = "transpiled_sabre.qasm"

# The final logical -> physical embedding after transpilation
# Format: {logical_qubit_index: physical_qubit_index}
EMBEDDING = {
  "0": 0,
  "1": 2,
  "2": 1,
  "3": 3
}
# ------------------------------------------------

def load_circuit(path):
    """Load a QuantumCircuit from a QASM2 file."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    return QuantumCircuit.from_qasm_file(path)

def reorder_qubits(circ, embedding):
    """
    Reorder qubits according to embedding (logical -> physical).
    
    Args:
        circ: QuantumCircuit with physical qubit ordering
        embedding: dict mapping {logical_index: physical_index}
        
    Returns:
        Circuit with logical qubit ordering (permuted)
    """
    num_qubits = circ.num_qubits
    
    # Create the inverse permutation: from physical to logical
    # physical_qubit -> logical_qubit
    inverse_embedding = [0] * num_qubits
    for logical_str, physical_str in embedding.items():
        logical = int(logical_str)
        physical = int(physical_str)
        if physical < num_qubits:
            inverse_embedding[physical] = logical
    
    # Create a new circuit with permuted qubits
    permuted_circ = QuantumCircuit(num_qubits, circ.num_clbits)
    
    # Copy metadata
    permuted_circ.metadata = circ.metadata.copy() if circ.metadata else {}
    
    # For each operation in the circuit
    for instruction, qargs, cargs in circ.data:
        # Map physical qubits to logical qubits
        # Get the index from the Qubit object by finding its position in the circuit
        mapped_qargs = []
        for qarg in qargs:
            # Get the qubit index
            # Method 1: Try to get from register
            qubit_index = None
            for i, qubit in enumerate(circ.qubits):
                if qubit == qarg:
                    qubit_index = i
                    break
            
            if qubit_index is not None and qubit_index < len(inverse_embedding):
                mapped_qargs.append(inverse_embedding[qubit_index])
            else:
                # If we can't find it, keep original (shouldn't happen)
                mapped_qargs.append(qarg)
        
        # Add the instruction with mapped qubits
        # We need to convert indices back to qubit objects
        mapped_qobj = [permuted_circ.qubits[idx] for idx in mapped_qargs]
        permuted_circ.append(instruction, mapped_qobj, cargs)
    
    return permuted_circ

def check_unitary_equivalence(circ1, circ2, atol=1e-10):
    """Check if two circuits are unitarily equivalent (strict)."""
    U1 = Operator(circ1).data
    U2 = Operator(circ2).data
    
    if np.allclose(U1, U2, atol=atol):
        print("✅ Circuits are UNITARY-equivalent (including global phase).")
        return True
    else:
        print("❌ Circuits are NOT unitarily equivalent!")
        diff = np.max(np.abs(U1 - U2))
        print(f"Max element-wise difference: {diff:e}")
        
        # Check if they're equivalent up to global phase
        phase = np.angle(np.trace(U1.conj().T @ U2))
        U2_adjusted = U2 * np.exp(-1j * phase)
        if np.allclose(U1, U2_adjusted, atol=atol):
            print(f"   But they ARE equivalent up to global phase φ = {phase:.6f} rad")
        
        return False

def check_statevector_equivalence(circ1, circ2, atol=1e-10):
    """Check if circuits produce the same quantum states (ignores global phase)."""
    sv1 = Statevector.from_instruction(circ1)
    sv2 = Statevector.from_instruction(circ2)
    
    # Calculate fidelity
    fidelity = np.abs(sv1.inner(sv2))
    
    if np.abs(fidelity - 1.0) < atol:
        print(f"✅ Statevector equivalence: fidelity = {fidelity:.15f}")
        return True
    else:
        print(f"❌ Statevector equivalence FAILED: fidelity = {fidelity:.15f}")
        
        # Show some diagnostic info
        prob1 = np.abs(sv1.data) ** 2
        prob2 = np.abs(sv2.data) ** 2
        max_prob_diff = np.max(np.abs(prob1 - prob2))
        avg_prob_diff = np.mean(np.abs(prob1 - prob2))
        
        print(f"   Max probability difference: {max_prob_diff:e}")
        print(f"   Average probability difference: {avg_prob_diff:e}")
        
        # Find states with largest differences
        if circ1.num_qubits <= 6:  # Only show for reasonably small circuits
            print("   Top 5 probability differences:")
            # Create list of (probability, difference, state_index) tuples
            differences = []
            for idx in range(len(prob1)):
                diff = abs(prob1[idx] - prob2[idx])
                if diff > atol:
                    differences.append((prob1[idx], prob2[idx], diff, idx))
            
            # Sort by difference (largest first)
            differences.sort(key=lambda x: x[2], reverse=True)
            
            # Show top 5
            for i in range(min(5, len(differences))):
                prob1_val, prob2_val, diff_val, idx = differences[i]
                bitstring = format(idx, f'0{circ1.num_qubits}b')
                print(f"     |{bitstring}⟩: {prob1_val:.6f} vs {prob2_val:.6f} (diff: {diff_val:.2e})")
        
        return False

def check_probability_distribution(circ1, circ2, atol=1e-10):
    """
    Check if measurement probability distributions are identical.
    This is the ultimate test for physical equivalence.
    """
    sv1 = Statevector.from_instruction(circ1)
    sv2 = Statevector.from_instruction(circ2)
    
    prob1 = np.abs(sv1.data) ** 2
    prob2 = np.abs(sv2.data) ** 2
    
    if np.allclose(prob1, prob2, atol=atol):
        print("✅ Probability distributions match exactly")
        return True
    else:
        print("❌ Probability distributions differ")
        
        max_diff = np.max(np.abs(prob1 - prob2))
        avg_diff = np.mean(np.abs(prob1 - prob2))
        
        print(f"   Max probability difference: {max_diff:e}")
        print(f"   Average probability difference: {avg_diff:e}")
        
        # Show the largest differences
        if circ1.num_qubits <= 6:
            print("   Largest differences:")
            # Get indices sorted by absolute difference
            diff_indices = np.argsort(np.abs(prob1 - prob2))[-5:]  # Top 5 differences
            for idx in diff_indices[::-1]:
                diff = abs(prob1[idx] - prob2[idx])
                if diff > atol:
                    bitstring = format(idx, f'0{circ1.num_qubits}b')
                    print(f"     |{bitstring}⟩: {prob1[idx]:.6f} vs {prob2[idx]:.6f} (diff: {diff:.2e})")
        
        return False

def main():
    normalized_path = os.path.join(CIRCUITS_FOLDER, NORMALIZED_QASM)
    transpiled_path = os.path.join(CIRCUITS_FOLDER, TRANSPILED_QASM)

    print("=" * 70)
    print("NORMALIZED vs TRANSPILED CIRCUIT EQUIVALENCE CHECK")
    print(f"Embedding: {EMBEDDING}")
    print("=" * 70)
    
    # Load circuits
    normalized_circ = load_circuit(normalized_path)
    transpiled_circ = load_circuit(transpiled_path)
    
    print(f"\nNormalized circuit: {NORMALIZED_QASM}")
    print(f"  Qubits: {normalized_circ.num_qubits}")
    print(f"  Gates: {normalized_circ.size()}")
    print(f"  Depth: {normalized_circ.depth()}")
    
    print(f"\nTranspiled circuit: {TRANSPILED_QASM}")
    print(f"  Qubits: {transpiled_circ.num_qubits}")
    print(f"  Gates: {transpiled_circ.size()}")
    print(f"  Depth: {transpiled_circ.depth()}")
    
    if normalized_circ.num_qubits != transpiled_circ.num_qubits:
        print(f"❌ Error: Number of qubits doesn't match!")
        print(f"  Normalized: {normalized_circ.num_qubits} qubits")
        print(f"  Transpiled: {transpiled_circ.num_qubits} qubits")
        sys.exit(1)
    
    # Apply embedding permutation to transpiled circuit
    print(f"\nApplying embedding permutation: {EMBEDDING}")
    transpiled_circ_permuted = reorder_qubits(transpiled_circ, EMBEDDING)
    
    # Check 1: Unitary equivalence
    print("\n" + "=" * 70)
    print("1. UNITARY EQUIVALENCE CHECK (strict)")
    print("-" * 70)
    unitary_ok = check_unitary_equivalence(normalized_circ, transpiled_circ_permuted)
    
    # Check 2: Statevector equivalence
    print("\n" + "=" * 70)
    print("2. STATEVECTOR EQUIVALENCE CHECK (ignores global phase)")
    print("-" * 70)
    statevector_ok = check_statevector_equivalence(normalized_circ, transpiled_circ_permuted)
    
    # Check 3: Probability distribution equivalence
    print("\n" + "=" * 70)
    print("3. PROBABILITY DISTRIBUTION CHECK")
    print("-" * 70)
    probability_ok = check_probability_distribution(normalized_circ, transpiled_circ_permuted)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"Unitary equivalence:        {'✅ PASS' if unitary_ok else '❌ FAIL'}")
    print(f"Statevector equivalence:    {'✅ PASS' if statevector_ok else '❌ FAIL'}")
    print(f"Probability distribution:   {'✅ PASS' if probability_ok else '❌ FAIL'}")
    
    if statevector_ok and probability_ok:
        print("\n🎉 Circuits are PHYSICALLY EQUIVALENT!")
        print("   (They will produce identical measurement outcomes)")
        if not unitary_ok:
            print("   Note: Circuits differ by a global phase only")
    else:
        print("\n⚠️ Circuits are NOT equivalent!")
        
        # Additional diagnostics
        if not statevector_ok:
            print("\n   SUGGESTIONS:")
            print("   1. Check if the embedding is correct")
            print("   2. Verify the transpilation preserved gate decompositions")
            print("   3. Look for optimization differences between circuits")

if __name__ == "__main__":
    main()