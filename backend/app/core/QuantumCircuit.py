from __future__ import annotations
from typing import List, Any, Dict, Optional
from qiskit import QuantumCircuit as QiskitQuantumCircuit
from qiskit.qasm3 import loads as qasm3_load


# ================================================================
# Base Operation
# ================================================================
class Operation:
    """Generic quantum operation."""
    def __init__(
        self,
        name: str,
        qubits: List[int],
        clbits: Optional[List[int]] = None,
        params: Optional[List[Any]] = None,
        condition: Optional["Condition"] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.qubits = qubits
        self.clbits = clbits or []
        self.params = params or []
        self.condition = condition
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Operation(name={self.name}, qubits={self.qubits}, params={self.params})"


# ================================================================
# Conditions (e.g., if (c == 1))
# ================================================================
class Condition:
    """Classical condition for conditional operations (current Qiskit versions)."""
    def __init__(self, creg: str, value: int):
        """
        Args:
            creg: Name of the classical register the condition applies to.
            value: Integer value of the condition (if creg == value).
        """
        self.creg = creg
        self.value = value

    def __repr__(self):
        return f"Condition(creg={self.creg!r}, value={self.value})"



# ================================================================
# Control Flow (QASM 3)
# ================================================================
class ForLoop(Operation):
    """For-loop control flow (QASM 3)."""
    def __init__(self, iterations: int, body: List[Operation]):
        super().__init__("for_loop", [], [])
        self.iterations = iterations
        self.body = body


class WhileLoop(Operation):
    """While-loop control flow (QASM 3)."""
    def __init__(self, condition: Condition, body: List[Operation]):
        super().__init__("while_loop", [], [])
        self.condition = condition
        self.body = body


class IfElse(Operation):
    """If/Else control flow (QASM 3)."""
    def __init__(
        self,
        condition: Condition,
        if_body: List[Operation],
        else_body: Optional[List[Operation]] = None
    ):
        super().__init__("if_else", [], [])
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body or []


# ================================================================
# Main IR Class
# ================================================================
class QuantumCircuit:
    """Vendor-independent representation of a quantum circuit."""

    def __init__(
        self,
        qubit_count: int = 0,
        clbit_count: int = 0,
        operations: Optional[List[Operation]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.qubit_count = qubit_count
        if isinstance(clbit_count, int):
            self.clbit_count = clbit_count
        elif isinstance(clbit_count, (list, tuple)):
            self.clbit_count = len(clbit_count)
        elif clbit_count is None:
            self.clbit_count = 0
        self.operations = operations or []
        self.metadata = metadata or {}
        print(f"Initialized QuantumCircuit with {self.qubit_count} qubits and {self.clbit_count} clbits.")

    # ------------------------------------------
    # Add operations
    # ------------------------------------------
    def add_operation(self, op: Operation):
        self.operations.append(op)

    def add_gate(self, name: str, qubits: List[int], params=None):
        self.operations.append(Operation(name, qubits, params=params))

    def add_measure(self, qubit: int, clbit: int):
        self.operations.append(Operation("measure", [qubit], [clbit]))

    def add_barrier(self, qubits: List[int]):
        self.operations.append(Operation("barrier", qubits))

    # ------------------------------------------
    # Control flow insertion
    # ------------------------------------------
    def add_for_loop(self, iterations: int, body: List[Operation]):
        self.operations.append(ForLoop(iterations, body))

    def add_while_loop(self, condition: Condition, body: List[Operation]):
        self.operations.append(WhileLoop(condition, body))

    def add_if_else(self, condition: Condition, if_body: List[Operation], else_body=None):
        self.operations.append(IfElse(condition, if_body, else_body))

    # ------------------------------------------
    # Serialization (e.g., for web apps)
    # ------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "qubit_count": self.qubit_count,
            "clbit_count": self.clbit_count,
            "operations": [self._op_to_dict(op) for op in self.operations],
            "metadata": self.metadata,
        }

    @staticmethod
    def _op_to_dict(op: Operation) -> Dict[str, Any]:
        base = {
            "type": op.name,
            "qubits": op.qubits,
            "clbits": op.clbits,
            "params": op.params,
            "metadata": op.metadata,
        }

        if op.condition:
            base["condition"] = {"clbit": op.condition.clbit, "value": op.condition.value}

        # Control flow special cases:
        if isinstance(op, ForLoop):
            base["iterations"] = op.iterations
            base["body"] = [QuantumCircuit._op_to_dict(o) for o in op.body]

        elif isinstance(op, WhileLoop):
            base["condition"] = {
                "clbit": op.condition.clbit,
                "value": op.condition.value,
            }
            base["body"] = [QuantumCircuit._op_to_dict(o) for o in op.body]

        elif isinstance(op, IfElse):
            base["condition"] = {
                "clbit": op.condition.clbit,
                "value": op.condition.value,
            }
            base["if_body"] = [QuantumCircuit._op_to_dict(o) for o in op.if_body]
            base["else_body"] = [QuantumCircuit._op_to_dict(o) for o in op.else_body]

        return base

    # ------------------------------------------
    # Deserialization
    # ------------------------------------------
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "QuantumCircuit":
        qc = QuantumCircuit(
            data["num_qubits"],
            data.get("clbit_count", 0),
            metadata=data.get("metadata", {}),
        )
        print(f"Loading QuantumCircuit from dict with {qc.qubit_count} qubits and {qc.clbit_count} clbits.")
        for op_data in data["gates"]:
            qc.operations.append(QuantumCircuit._op_from_dict(op_data))

        return qc

    @staticmethod
    def _op_from_dict(data: Dict[str, Any]) -> Operation:
        t = data["name"]

        if t == "for_loop":
            body = [QuantumCircuit._op_from_dict(o) for o in data["body"]]
            return ForLoop(data["iterations"], body)

        if t == "while_loop":
            cond = Condition(data["condition"]["clbit"], data["condition"]["value"])
            body = [QuantumCircuit._op_from_dict(o) for o in data["body"]]
            return WhileLoop(cond, body)

        if t == "if_else":
            cond = Condition(data["condition"]["clbit"], data["condition"]["value"])
            if_body = [QuantumCircuit._op_from_dict(o) for o in data["if_body"]]
            else_body = [QuantumCircuit._op_from_dict(o) for o in data["else_body"]]
            return IfElse(cond, if_body, else_body)

        # Default: normal operation
        cond = None
        if "condition" in data and data["condition"]:
            cond = Condition(data["condition"]["clbit"], data["condition"]["value"])

        return Operation(
            data.get("name", []),
            data.get("qubits", []),
            data.get("clbits", []),
            data.get("params", []),
            cond,
            data.get("metadata", {}),
        )
    # ------------------------------------------
    # Qiskit interop to QuantumCircuit
    # ------------------------------------------
    def from_qiskit(qc):
        qCal_qc = QuantumCircuit(
            qubit_count=qc.num_qubits,
            clbit_count=qc.num_clbits
        )
        for instr, qargs, cargs in qc.data:
            print(f"Processing instruction: {instr.name} on qubits {qargs} and classical args {cargs}")
            name = instr.name
            params = [float(p) for p in instr.params]
            qubits = [qc.qubits.index(q) for q in qargs]
            clbits = [qc.clbits.index(c) for c in cargs]
            print(f"Mapped qubit: {qubits}")
            print(f"Mapped clbit: {clbits}")

            # support classical conditions
            condition = None

            if getattr(instr, "condition", None) is not None:
                creg, val = instr.condition
                condition = Condition(
                    creg=creg.name,        # name of the classical register
                    value=val
                )


            qCal_qc.add_operation(Operation(
                name=name,
                qubits=qubits,
                clbits=clbits,
                params=params,
                condition=condition
            ))
        print("Converted Qiskit QuantumCircuit to IR QuantumCircuit")
        return qCal_qc

    @staticmethod
    def load_qasm2(qasm2_str: str) -> QuantumCircuit:
        """
        Load an OpenQASM 2.0 string into a Qiskit QuantumCircuit.
        """
        try:
            qiskit_qc = QiskitQuantumCircuit.from_qasm_str(qasm2_str)
            return QuantumCircuit.from_qiskit(qiskit_qc)
        except Exception as e:
            raise ValueError(f"Failed to parse QASM2: {e}")
    
    @staticmethod
    def load_qasm3(qasm3_str: str) -> QuantumCircuit:
        """
        Load an OpenQASM 3.0 string into a Qiskit QuantumCircuit.
        """
        try:
            qiskit_qc = qasm3_load(qasm3_str)
            return QuantumCircuit.from_qiskit(qiskit_qc)
        except Exception as e:
            raise ValueError(f"Failed to parse QASM3: {e}")
        
    @staticmethod
    def load_json(json_dict: dict) -> QuantumCircuit:
        """
        Load a Qiskit-style JSON/dict into a QuantumCircuit.
        """
        try:
            return QuantumCircuit.from_dict(json_dict)
        except Exception as e:
            raise ValueError(f"Failed to load JSON circuit: {e}")

