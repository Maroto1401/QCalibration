from qiskit_ibm_runtime import QiskitRuntimeService
from uuid import uuid4
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

def fetch_ibm_topologies() -> List[Dict]:
    """
    Fetch all available IBM Quantum backends and return JSON-safe TopologyCard dicts.
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

        # Safe instructions: convert any Qiskit object to string
        safe_instructions = [str(instr) for instr in getattr(backend, "instructions", [])]

        # Safe gates
        safe_gates = []
        for g in getattr(properties, "gates", []):
            safe_gates.append({
                "name": getattr(g, "gate", str(g)),
                "qubits": getattr(g, "qubits", []),
                "gate_error": next(
                    (p.value for p in getattr(g, "parameters", []) if getattr(p, "name", "") == "gate_error"),
                    None
                ),
                "duration": next(
                    (p.value for p in getattr(g, "parameters", []) if getattr(p, "name", "") in ["gate_length", "duration"]),
                    None
                ),
                "parameters": {getattr(p, "name", str(p)): getattr(p, "value", None) for p in getattr(g, "parameters", [])}
            })

        # Safe qubits
        safe_qubits = []
        for i, q in enumerate(getattr(properties, "qubits", [])):
            safe_qubits.append({
                "qubit": i,
                "t1": q[0].value if len(q) > 0 else None,
                "t2": q[1].value if len(q) > 1 else None,
                "frequency": q[2].value if len(q) > 2 else None,
                "readout_error": q[3].value if len(q) > 3 else None,
            })

        topology = {
            "id": str(uuid4()),
            "name": backend.name,
            "vendor": "IBM",
            "releaseDate": str(backend.backend_version),
            "available": status.operational,
            "description": f"{config.n_qubits}-qubit backend",
            "coupling_map": config.coupling_map,  # list of tuples
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

    Args:
        coupling_map: list of 2-tuples representing connections between qubits
        num_qubits: total number of qubits

    Returns:
        str: 'low', 'medium', 'high', or 'very high'
    """
    if num_qubits <= 1:
        return "low"

    # Count connections per qubit
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
