import os
import numpy as np
import pandas as pd

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_aer import AerSimulator

# =====================================================
# Configuration
# =====================================================
CIRCUIT_FOLDER = "circuits"
OUTPUT_FOLDER = "output"
TRANSPILATION_TARGETS = {"logical_circuit.qasm", "normalized.qasm"}
SHOTS = 4096

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =====================================================
# Load IBM backend for properties
# =====================================================
service = QiskitRuntimeService()
backend = service.backend("ibm_torino")
backend_props = backend.properties()

# =====================================================
# Helper functions
# =====================================================
def load_qasm_circuits(folder):
    circuits = {}
    for fname in os.listdir(folder):
        if fname.endswith(".qasm"):
            path = os.path.join(folder, fname)
            circuit = QuantumCircuit.from_qasm_file(path)
            
            # Add measurements if not present
            if len(circuit.cregs) == 0:
                circuit.measure_all()
            
            circuits[fname] = circuit
    return circuits

def ideal_probabilities(circuit):
    sv = Statevector.from_instruction(circuit)
    return sv.probabilities_dict()

def classical_fidelity(p_ideal, p_exp):
    keys = set(p_ideal.keys()).union(p_exp.keys())
    return sum(np.sqrt(p_ideal.get(k,0) * p_exp.get(k,0)) for k in keys) ** 2

def estimate_runtime(circuit, backend_props):
    runtime = 0.0
    for inst, qargs, _ in circuit.data:
        try:
            runtime += backend_props.gate_length(inst.name, [q.index for q in qargs])
        except Exception:
            pass
    return runtime

def extract_backend_metrics(circuit, backend_props):
    qubits = {q.index for q in circuit.qubits}
    t1s, t2s, readout_errs, gate_errs = [], [], [], []

    for q in qubits:
        t1_val = backend_props.t1(q)
        t2_val = backend_props.t2(q)
        
        if hasattr(t1_val, 'value'):
            t1_val = t1_val.value
        if hasattr(t2_val, 'value'):
            t2_val = t2_val.value
            
        t1s.append(t1_val)
        t2s.append(t2_val)
        
        readout_err = backend_props.readout_error(q)
        if hasattr(readout_err, 'value'):
            readout_err = readout_err.value
        readout_errs.append(readout_err)

    for inst, qargs, _ in circuit.data:
        try:
            gate_err = backend_props.gate_error(inst.name, [q.index for q in qargs])
            if hasattr(gate_err, 'value'):
                gate_err = gate_err.value
            gate_errs.append(gate_err)
        except Exception:
            pass

    return {
        "avg_gate_error": np.mean(gate_errs) if gate_errs else None,
        "avg_readout_error": np.mean(readout_errs),
        "t1_avg": np.mean(t1s),
        "t2_avg": np.mean(t2s),
    }

def decoherence_fidelity(runtime, t1, t2):
    """Calculate decoherence fidelity estimate"""
    if t1 is None or t2 is None or t1 <= 0 or t2 <= 0:
        return None
    return min(np.exp(-runtime / t1), np.exp(-runtime / t2))

# =====================================================
# Load circuits
# =====================================================
circuits = load_qasm_circuits(CIRCUIT_FOLDER)
results = []

# Create simulator backend
simulator = AerSimulator()

# =====================================================
# Run on real hardware
# =====================================================
print("Running on real hardware (IBM Torino)...")
sampler_real = Sampler(mode=backend)
sampler_real.options.default_shots = SHOTS

for name, circuit in circuits.items():
    print(f"Processing circuit: {name}")
    opt_levels = [0, 1, 2, 3] if name in TRANSPILATION_TARGETS else [None]
    ideal_probs = ideal_probabilities(circuit)

    for opt in opt_levels:
        # Transpile using generate_preset_pass_manager
        if opt is not None:
            pm = generate_preset_pass_manager(backend=backend, optimization_level=opt)
            tcirc = pm.run(circuit)
        else:
            tcirc = circuit.copy()

        # Execute circuit on ibm_torino
        try:
            job = sampler_real.run([tcirc])
            result = job.result()
            pub_result = result[0]
            
            # Extract counts from DataBin
            if hasattr(pub_result.data, 'meas'):
                exp_probs = pub_result.data.meas.get_counts()
                # Convert counts to probabilities
                total_shots = sum(exp_probs.values())
                exp_probs = {k: v/total_shots for k, v in exp_probs.items()}
            else:
                print(f"  ✗ Opt level {opt}: No measurement data in result")
                continue

            # Metrics
            fid = classical_fidelity(ideal_probs, exp_probs)
            runtime = estimate_runtime(tcirc, backend_props)
            metrics = extract_backend_metrics(tcirc, backend_props)
            deco_fid = decoherence_fidelity(runtime, metrics["t1_avg"], metrics["t2_avg"])

            results.append({
                "run_type": "real",
                "circuit": name,
                "optimization_level": opt,
                "depth": tcirc.depth(),
                "gate_count": tcirc.size(),
                "runtime_s": runtime,
                "classical_fidelity": fid,
                "avg_gate_error": metrics["avg_gate_error"],
                "avg_readout_error": metrics["avg_readout_error"],
                "t1_avg": metrics["t1_avg"],
                "t2_avg": metrics["t2_avg"],
                "decoherence_fidelity_est": deco_fid,
                "decoherence_risk": deco_fid < 0.99 if deco_fid is not None else None
            })
            print(f"  ✓ Opt level {opt}: Fidelity = {fid:.4f}")
        except Exception as e:
            print(f"  ✗ Opt level {opt} failed: {e}")

# =====================================================
# Run on simulator
# =====================================================
print("\nRunning on simulator (AerSimulator)...")
sampler_sim = Sampler(mode=simulator)
sampler_sim.options.default_shots = SHOTS

for name, circuit in circuits.items():
    print(f"Processing circuit: {name}")
    opt_levels = [0, 1, 2, 3] if name in TRANSPILATION_TARGETS else [None]
    ideal_probs = ideal_probabilities(circuit)

    for opt in opt_levels:
        if opt is not None:
            pm = generate_preset_pass_manager(backend=simulator, optimization_level=opt)
            tcirc = pm.run(circuit)
        else:
            tcirc = circuit.copy()

        try:
            job = sampler_sim.run([tcirc])
            result = job.result()
            pub_result = result[0]
            
            # Extract counts from DataBin
            if hasattr(pub_result.data, 'meas'):
                exp_probs = pub_result.data.meas.get_counts()
                # Convert counts to probabilities
                total_shots = sum(exp_probs.values())
                exp_probs = {k: v/total_shots for k, v in exp_probs.items()}
            else:
                print(f"  ✗ Opt level {opt}: No measurement data in result")
                continue

            fid = classical_fidelity(ideal_probs, exp_probs)
            
            results.append({
                "run_type": "simulator",
                "circuit": name,
                "optimization_level": opt,
                "depth": tcirc.depth(),
                "gate_count": tcirc.size(),
                "runtime_s": None,
                "classical_fidelity": fid,
                "avg_gate_error": None,
                "avg_readout_error": None,
                "t1_avg": None,
                "t2_avg": None,
                "decoherence_fidelity_est": None,
                "decoherence_risk": None
            })
            print(f"  ✓ Opt level {opt}: Fidelity = {fid:.4f}")
        except Exception as e:
            print(f"  ✗ Opt level {opt} failed: {e}")

# =====================================================
# Save results to CSV
# =====================================================
print("\nSaving results...")
df = pd.DataFrame(results)
csv_path = os.path.join(OUTPUT_FOLDER, "results_summary.csv")
df.to_csv(csv_path, index=False)

print(f"Results saved to {csv_path}")
print(f"Total results: {len(results)}")