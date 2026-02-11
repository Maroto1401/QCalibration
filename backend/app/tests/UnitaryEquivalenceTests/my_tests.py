from qiskit_ibm_runtime import QiskitRuntimeService

# Replace with your IBM Quantum API token
QiskitRuntimeService.save_account(channel="ibm_quantum", token="gkVY6Gxx3Gfm3Natc_jlA91j0sw2iF-NJz-Zg2mdeTqQ", overwrite=True)


from qiskit import QuantumCircuit

qc_logical = QuantumCircuit.from_qasm_file("logical.qasm")
qc_custom  = QuantumCircuit.from_qasm_file("my_transpiled.qasm")

from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(channel="ibm_quantum")

backend = service.backend("ibm_marrakesh")  

# Example: logical → physical qubit mapping
embedding = {0: 3, 1: 5, 2: 7}

qc_custom = qc_custom.assign_qubit_mapping(embedding)

from qiskit_ibm_runtime import Sampler

sampler = Sampler(backend=backend)

job_logical = sampler.run(
    qc_logical,
    shots=1024,
    skip_transpilation=True
)

job_custom = sampler.run(
    qc_custom,
    shots=1024,
    skip_transpilation=True
)

def extract_job_metrics(job):
    metrics = job.metrics()
    return {
        "job_id": job.job_id(),
        "status": job.status().name,
        "queue_time_s": metrics.get("queue_time", None),
        "execution_time_s": metrics.get("execution_time", None),
        "estimated_cost": metrics.get("estimated_cost", None),
        "shots": metrics.get("shots", None),
    }

logical_metrics = extract_job_metrics(job_logical)
custom_metrics  = extract_job_metrics(job_custom)

print("Logical circuit:", logical_metrics)
print("Custom circuit:", custom_metrics)

from qiskit import transpile

qc_qiskit = transpile(
    qc_logical,
    backend=backend,
    optimization_level=3
)

job_qiskit = sampler.run(
    qc_qiskit,
    shots=1024,
    skip_transpilation=True
)

qiskit_metrics = extract_job_metrics(job_qiskit)
print("Qiskit transpiled:", qiskit_metrics)

