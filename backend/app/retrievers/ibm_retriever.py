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

    for backend in service.backends(simulator=False):
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
            "minQubits": config.n_qubits,
            "maxQubits": config.n_qubits,
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
    Classify connectivity of a backend as 'low', 'medium', or 'high'.

    Args:
        coupling_map: list of 2-tuples representing connections between qubits
        num_qubits: total number of qubits

    Returns:
        str: 'low', 'medium', or 'high'
    """
    if num_qubits <= 1:
        return "low"

    max_edges = num_qubits * (num_qubits - 1) / 2  # fully connected graph
    actual_edges = len(coupling_map)

    connectivity_ratio = actual_edges / max_edges

    if connectivity_ratio < 0.3:
        return "low"
    elif connectivity_ratio < 0.7:
        return "medium"
    else:
        return "high"
