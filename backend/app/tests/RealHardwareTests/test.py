import os
import numpy as np
import pandas as pd

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_aer import AerSimulator

# =====================================================
# Configuration
# =====================================================
CIRCUIT_FOLDER = "circuits"
OUTPUT_FOLDER = "output"
REFERENCE_CIRCUIT = "logical_circuit.qasm"
TRANSPILATION_TARGETS = {"logical_circuit.qasm", "normalized.qasm"}
SHOTS = 4096

# Logical → Physical mapping
EMBEDDINGS = {
    "naive_transpiled.qasm": {"0": 0, "1": 1, "2": 2, "3": 3},
    "sabre_transpiled.qasm": {"0": 0, "1": 3, "2": 1, "3": 2},
    "dynamic_transpiled.qasm": {"0": 1, "1": 3, "2": 0, "3": 2},
    "calibration_transpiled.qasm": {"0": 28, "1": 36, "2": 29, "3": 30},
    "normalized.qasm": {"0": 0, "1": 1, "2": 2, "3": 3},
}

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =====================================================
# Backend
# =====================================================
service = QiskitRuntimeService()
backend = service.backend("ibm_torino")
backend_props = backend.properties()

simulator = AerSimulator()

# =====================================================
# Helpers
# =====================================================

def load_qasm_circuits(folder):
    circuits = {}
    for fname in os.listdir(folder):
        if fname.endswith(".qasm"):
            path = os.path.join(folder, fname)
            circ = QuantumCircuit.from_qasm_file(path)
            if len(circ.cregs) == 0:
                circ.measure_all()
            circuits[fname] = circ
    return circuits


def remove_measurements(circuit):
    qc = QuantumCircuit(circuit.num_qubits)
    for instr in circuit.data:
        if instr.operation.name != "measure":
            qc.append(instr.operation, instr.qubits)
    return qc


def ideal_probabilities(circuit):
    circ_no_meas = remove_measurements(circuit)
    sv = Statevector.from_instruction(circ_no_meas)
    return sv.probabilities_dict()


def classical_fidelity(p_ideal, p_exp):
    keys = set(p_ideal.keys()).union(p_exp.keys())
    return sum(np.sqrt(p_ideal.get(k, 0) * p_exp.get(k, 0)) for k in keys) ** 2


def circuits_equivalent(c1, c2):
    c1u = remove_measurements(c1)
    c2u = remove_measurements(c2)
    try:
        return Operator(c1u).equiv(Operator(c2u))
    except Exception:
        return False


def apply_inverse_embedding(circuit, embedding):
    """
    Undo logical→physical mapping.
    embedding: {logical: physical}
    """

    embedding = {int(k): int(v) for k, v in embedding.items()}

    # Reverse map: physical → logical
    phys_to_logical = {v: k for k, v in embedding.items()}

    n = circuit.num_qubits
    corrected = QuantumCircuit(n)

    corrected.compose(circuit, inplace=True)

    # Build permutation list
    perm = list(range(n))

    for physical, logical in phys_to_logical.items():
        if physical < n:
            perm[physical] = logical

    # Apply permutation using swaps
    for i in range(n):
        while perm[i] != i:
            j = perm[i]
            corrected.swap(i, j)
            perm[i], perm[j] = perm[j], perm[i]

    corrected.measure_all()

    return corrected

def run_sampler(sampler, circuit):
    job = sampler.run([circuit])
    result = job.result()[0]

    if hasattr(result.data, "c"):
        counts = result.data.c.get_counts()
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}
    else:
        return None


# =====================================================
# Load circuits
# =====================================================
circuits = load_qasm_circuits(CIRCUIT_FOLDER)
reference = circuits[REFERENCE_CIRCUIT]
ideal_reference_probs = ideal_probabilities(reference)

results = []

# =====================================================
# Simulator Validation First
# =====================================================
print("Validating logical equivalence on simulator...")

sampler_sim = Sampler(mode=simulator)
sampler_sim.options.default_shots = SHOTS

validated_circuits = {}

for name, circuit in circuits.items():
    print(f"\nChecking {name}")

    embedding = EMBEDDINGS.get(name)
    if embedding:
        circuit = apply_inverse_embedding(circuit, embedding)


    # Check unitary equivalence
    eq = circuits_equivalent(reference, circuit)
    print(f"  Unitary equivalent to reference? {eq}")

    # Simulator fidelity check
    exp_probs = run_sampler(sampler_sim, circuit)
    fid = classical_fidelity(ideal_reference_probs, exp_probs)
    print(f"  Simulator fidelity: {fid:.6f}")

    if fid < 0.99:
        print("  ❌ Logical mismatch. Skipping hardware execution.")
    else:
        validated_circuits[name] = circuit
        print("  ✅ Passed validation.")

# =====================================================
# Real Hardware Execution
# =====================================================
print("\nRunning validated circuits on real hardware...")

sampler_real = Sampler(mode=backend)
sampler_real.options.default_shots = SHOTS

for name, circuit in validated_circuits.items():
    print(f"\nProcessing {name}")

    opt_levels = [0, 1, 2, 3] if name in TRANSPILATION_TARGETS else [None]

    for opt in opt_levels:
        if opt is not None:
            pm = generate_preset_pass_manager(
                backend=backend,
                optimization_level=opt
            )
            tcirc = pm.run(circuit)
        else:
            pm = generate_preset_pass_manager(
                backend=backend,
                optimization_level=1
            )
            tcirc = pm.run(circuit)

        try:
            exp_probs = run_sampler(sampler_real, tcirc)
            fid = classical_fidelity(ideal_reference_probs, exp_probs)

            results.append({
                "circuit": name,
                "optimization_level": opt,
                "depth": tcirc.depth(),
                "gate_count": tcirc.size(),
                "classical_fidelity": fid
            })

            print(f"  ✓ Opt {opt}: Fidelity = {fid:.4f}")

        except Exception as e:
            print(f"  ✗ Opt {opt} failed: {e}")

# =====================================================
# Save Results
# =====================================================
df = pd.DataFrame(results)
csv_path = os.path.join(OUTPUT_FOLDER, "results_summary.csv")
df.to_csv(csv_path, index=False)

print("\nResults saved to:", csv_path)
print("Total hardware runs:", len(results))
