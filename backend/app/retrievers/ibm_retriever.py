from qiskit_ibm_runtime import QiskitRuntimeService
from uuid import uuid4
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

def fetch_ibm_topologies() -> List[Dict]:
    """
    Fetch all available IBM Quantum backends and return JSON-safe TopologyCard dicts
    with gate durations in seconds and qubit properties in proper units.
    """
    load_dotenv()
    service = QiskitRuntimeService(
        token=os.environ["IBM_QUANTUM_API_KEY"],
        instance=os.environ["IBM_QUANTUM_CRN"]
    )
    topologies = []
    backends = service.backends(simulator=False)
    
    for backend in backends:

        config = backend.configuration()
        status = backend.status()
        properties = backend.properties()
        dt = getattr(config, "dt", 1.0)  # dt in seconds

        # Safe instructions
        safe_instructions = [str(instr) for instr in getattr(backend, "instructions", [])]

        # Safe gates with duration in seconds
        safe_gates = []

        for g in getattr(properties, "gates", []):
            duration_dt = next(
                (p.value for p in getattr(g, "parameters", []) if getattr(p, "name", "") in ["gate_length", "duration"]),
                None
            )
            duration_seconds = duration_dt * dt if duration_dt is not None else None
            gate_error = next(
                (p.value for p in getattr(g, "parameters", []) if getattr(p, "name", "") == "gate_error"),
                None
            )

            safe_gates.append({
                "name": getattr(g, "gate", str(g)),
                "qubits": getattr(g, "qubits", []),
                "gate_error": gate_error,
                "duration": duration_seconds,
                "parameters": {getattr(p, "name", str(p)): getattr(p, "value", None) for p in getattr(g, "parameters", [])}
            })

        # Safe qubits
        safe_qubits = []
        for i, qubit_params in enumerate(getattr(properties, "qubits", [])):
            t1 = next((p.value for p in qubit_params if getattr(p, "name", "") == "T1"), None)
            t2 = next((p.value for p in qubit_params if getattr(p, "name", "") == "T2"), None)
            freq = next((p.value for p in qubit_params if getattr(p, "name", "") == "frequency"), None)
            readout_error = next((p.value for p in qubit_params if getattr(p, "name", "") == "readout_error"), None)
            safe_qubits.append({
                "qubit": i,
                "t1": t1 * 1e-6,                # seconds
                "t2": t2 * 1e-6,                # seconds
                "frequency": freq,       # Hz
                "readout_error": readout_error
            })

        topology = {
            "id": str(uuid4()),
            "name": backend.name,
            "vendor": "IBM",
            "releaseDate": str(backend.backend_version),
            "available": status.operational,
            "description": f"{config.n_qubits}-qubit backend",
            "topology_layout": "heavy-hex",
            "coupling_map": config.coupling_map,
            "connectivity": classify_connectivity(config.coupling_map, config.n_qubits),
            "numQubits": config.n_qubits,
            "basisGates": getattr(config, "basis_gates", []),
            "instructions": safe_instructions,
            "calibrationData": {
                "qubits": safe_qubits,
                "gates": safe_gates,
            },
        }
        print(f"Fetched IBM backend: {backend.name}")
        topologies.append(topology)

    return topologies


def classify_connectivity(coupling_map: List[Tuple[int, int]], num_qubits: int) -> str:
    """
    Classify connectivity of a backend based on average connections per qubit.
    """
    if num_qubits <= 1:
        return "low"

    connection_counts = [0] * num_qubits
    for q1, q2 in coupling_map:
        connection_counts[q1] += 1
        connection_counts[q2] += 1

    avg_connections = sum(connection_counts) / num_qubits

    if avg_connections < 3:
        return "low"
    elif avg_connections < 5:
        return "medium"
    elif avg_connections < 8:
        return "high"
    else:
        return "very high"
