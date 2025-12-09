class QuantumCircuit:
    def __init__(self):
        self.num_qubits = 0
        self.gates = []

    def load_from_qasm(self, qasm_text: str):
        # TODO implement your real QASM parsing logic
        self.num_qubits = 4
        self.gates = ["h 0", "cx 0 1"]

    def load_from_json(self, data: dict):
        self.num_qubits = data.get("num_qubits", 0)
        self.gates = data.get("gates", [])

    def to_dict(self):
        return {
            "num_qubits": self.num_qubits,
            "gates": self.gates,
        }
