# QASM 2 parser - converts QASM 2 text to internal QuantumCircuit representation
from ..core.QuantumCircuit import QuantumCircuit

def qasm2_parser(text: str) -> QuantumCircuit:
    """Parse QASM 2 text format into QuantumCircuit object."""
    return QuantumCircuit.load_qasm2(text)
