import json
from ..core.QuantumCircuit import QuantumCircuit

def parse_json(text: str) -> QuantumCircuit:
    """
    Parses JSON-based quantum circuit.
    """
    data = json.loads(text)
    return QuantumCircuit.load_json(data)
