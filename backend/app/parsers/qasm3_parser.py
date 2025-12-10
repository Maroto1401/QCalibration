from ..core.QuantumCircuit import QuantumCircuit

def qasm3_parser(text: str) -> QuantumCircuit:
    """
    Parses QASM 3 text.
    """
    return QuantumCircuit.load_qasm3(text)
