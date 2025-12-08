from typing import List, Dict, Any

class QuantumInstruction:
    """
    A single quantum operation in the unified circuit representation.
    """
    def __init__(self, name: str, qubits: List[int], params: List[float] = None):
        self.name = name
        self.qubits = qubits
        self.params = params or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "qubits": self.qubits,
            "params": self.params
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return QuantumInstruction(
            name=data["name"],
            qubits=data["qubits"],
            params=data.get("params", [])
        )


class QuantumCircuit:
    """
    Framework-agnostic internal representation of a quantum circuit.
    Every parser (QASM, Quil, Cirq JSON, QPY, .circ, etc.) converts into this class.
    """
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.instructions: List[QuantumInstruction] = []
        self.metadata: Dict[str, Any] = {}

    # Add instruction
    def add_gate(self, name: str, qubits: List[int], params: List[float] = None):
        if any(q >= self.num_qubits or q < 0 for q in qubits):
            raise ValueError("Qubit index out of range.")
        self.instructions.append(QuantumInstruction(name, qubits, params))

    # Export to dict (ready for JSON storage)
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_qubits": self.num_qubits,
            "instructions": [inst.to_dict() for inst in self.instructions],
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        qc = QuantumCircuit(data["num_qubits"])
        qc.metadata = data.get("metadata", {})
        for inst in data["instructions"]:
            qc.instructions.append(QuantumInstruction.from_dict(inst))
        return qc

    # Simple summary
    def summary(self) -> str:
        return (f"QuantumCircuit(qubits={self.num_qubits}, "
                f"gates={len(self.instructions)})")
