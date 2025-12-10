from ..core.QuantumCircuit import QuantumCircuit

def qasm2_parser(text: str) -> QuantumCircuit:
    """
    Parses QASM 2 text.
    """
    return QuantumCircuit.load_qasm2(text)
