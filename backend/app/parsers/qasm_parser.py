from ..core.QuantumCircuit import QuantumCircuit

def parse_qasm(text: str) -> QuantumCircuit:
    """
    Parses QASM 2 or QASM 3 text.
    Replace with your real parsing logic.
    """
    # Example stub — you will replace with real parser logic
    qc = QuantumCircuit()
    qc.load_from_qasm(text)
    return qc
