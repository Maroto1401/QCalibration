# QASM 2.0 exporter - converts internal circuit representation to OpenQASM 2.0 format
"""
Convert custom QuantumCircuit IR to OpenQASM 2.0 format.
"""
from typing import Set
from .QuantumCircuit import QuantumCircuit, Operation, ForLoop, WhileLoop, IfElse


class QASM2Exporter:
    """Exports a custom QuantumCircuit IR to OpenQASM 2.0 string."""
    
    # Standard gate parameters (gates that don't need explicit parameter declaration)
    PARAMETERLESS_GATES = {
        "x", "y", "z",
        "h", "s", "t",
        "sx", "sy",
        "id", "i",
        "cx", "cnot",
        "cy", "cz",
        "swap", "iswap",
        "measure",
        "barrier",
        "reset"
    }
    
    # Single-qubit parameterized gates
    SINGLE_PARAM_GATES = {"rx", "ry", "rz", "phase", "u1"}
    
    # Two-qubit parameterized gates
    TWO_PARAM_GATES = {"xx", "yy", "zz"}
    
    # Three-parameter universal gates
    THREE_PARAM_GATES = {"u", "u3"}
    
    def __init__(self, include_header: bool = True):
        """
        Args:
            include_header: Whether to include 'OPENQASM 2.0;' header
        """
        self.include_header = include_header
        self.declared_qregs: Set[str] = set()
        self.declared_cregs: Set[str] = set()
    
    def export(self, qc: QuantumCircuit) -> str:
        """
        Convert a QuantumCircuit to QASM2 string.
        
        Args:
            qc: Custom QuantumCircuit IR to export
            
        Returns:
            OpenQASM 2.0 formatted string
        """
        lines = []
        
        # Header
        if self.include_header:
            lines.append("OPENQASM 2.0;")
            lines.append('include "qelib1.inc";')
            lines.append("")
        
        # Register declarations
        if qc.num_qubits > 0:
            lines.append(f"qreg q[{qc.num_qubits}];")
            self.declared_qregs.add("q")
        
        if qc.num_clbits > 0:
            lines.append(f"creg c[{qc.num_clbits}];")
            self.declared_cregs.add("c")
        
        if qc.num_qubits > 0 or qc.num_clbits > 0:
            lines.append("")
        for i, op in enumerate(qc.operations):
            if op.name.lower() == "rz" and (not op.params or len(op.params) == 0):
                raise RuntimeError(f"Found rz without params at operation #{i}: {op}")
        # Operations
        for op in qc.operations:
            qasm_op = self._operation_to_qasm2(op)
            if qasm_op:
                lines.append(qasm_op)
        

        return "\n".join(lines)
    
    def _operation_to_qasm2(self, op: Operation, indent: int = 0) -> str:
        """
        Convert a single operation to QASM2.
        
        Args:
            op: Operation to convert
            indent: Indentation level (for nested control flow)
            
        Returns:
            QASM2 string for the operation
        """
        indent_str = "  " * indent
        
        # Handle control flow
        if isinstance(op, ForLoop):
            return self._for_loop_to_qasm2(op, indent)
        
        if isinstance(op, WhileLoop):
            return self._while_loop_to_qasm2(op, indent)
        
        if isinstance(op, IfElse):
            return self._if_else_to_qasm2(op, indent)
        
        # Handle barriers
        if op.name == "barrier":
            if op.qubits:
                qubits_str = ", ".join(f"q[{q}]" for q in op.qubits)
                return f"{indent_str}barrier {qubits_str};"
            else:
                return f"{indent_str}barrier;"
        
        # Handle measurements
        if op.name == "measure":
            if len(op.qubits) != 1 or len(op.clbits) != 1:
                raise ValueError(f"Measure operation must have exactly 1 qubit and 1 clbit")
            q = op.qubits[0]
            c = op.clbits[0]
            return f"{indent_str}measure q[{q}] -> c[{c}];"
        
        # Handle reset
        if op.name == "reset":
            if len(op.qubits) != 1:
                raise ValueError(f"Reset operation must have exactly 1 qubit")
            q = op.qubits[0]
            return f"{indent_str}reset q[{q}];"
        
        # Handle standard gates
        return self._gate_to_qasm2(op, indent_str)
    
    def _gate_to_qasm2(self, op: Operation, indent_str: str) -> str:
        """Convert a gate operation to QASM2."""
        gate_name = op.name.lower()
        qubits_str = ", ".join(f"q[{q}]" for q in op.qubits)
        
        # Parameterless gates
        if gate_name in self.PARAMETERLESS_GATES:
            return f"{indent_str}{gate_name} {qubits_str};"
        
        # Single-parameter gates (rx, ry, rz, u1, phase)
        if gate_name in self.SINGLE_PARAM_GATES:
            if not op.params or len(op.params) < 1:
                raise ValueError(f"{gate_name} requires at least 1 parameter")
            param = op.params[0]
            return f"{indent_str}{gate_name}({param}) {qubits_str};"
        
        # Two-parameter gates (xx, yy, zz)
        if gate_name in self.TWO_PARAM_GATES:
            if not op.params or len(op.params) < 2:
                raise ValueError(f"{gate_name} requires at least 2 parameters")
            param1, param2 = op.params[0], op.params[1]
            return f"{indent_str}{gate_name}({param1}, {param2}) {qubits_str};"
        
        # Three-parameter gates (u, u3)
        if gate_name in self.THREE_PARAM_GATES:
            if not op.params or len(op.params) < 3:
                raise ValueError(f"{gate_name} requires at least 3 parameters")
            param1, param2, param3 = op.params[0], op.params[1], op.params[2]
            return f"{indent_str}{gate_name}({param1}, {param2}, {param3}) {qubits_str};"
        
        # Custom gates or unknown gates (assume no parameters)
        if not op.params:
            return f"{indent_str}{gate_name} {qubits_str};"
        
        # Custom gates with parameters
        params_str = ", ".join(str(p) for p in op.params)
        return f"{indent_str}{gate_name}({params_str}) {qubits_str};"
    
    def _for_loop_to_qasm2(self, loop: ForLoop, indent: int) -> str:
        """Convert a for-loop to QASM2 (requires QASM 3.0, but we'll try to represent it)."""
        indent_str = "  " * indent
        lines = []
        
        # Note: QASM 2.0 doesn't have for loops, so we expand them
        # This is a limitation - ideally use QASM 3.0 for control flow
        lines.append(f"{indent_str}// for loop ({loop.iterations} iterations)")
        
        for i in range(loop.iterations):
            for op in loop.body:
                qasm_op = self._operation_to_qasm2(op, indent)
                if qasm_op:
                    lines.append(qasm_op)
        
        return "\n".join(lines)
    
    def _while_loop_to_qasm2(self, loop: WhileLoop, indent: int) -> str:
        """Convert a while-loop to QASM2 (not supported in QASM 2.0)."""
        indent_str = "  " * indent
        # QASM 2.0 doesn't support while loops
        lines = [
            f"{indent_str}// QASM 2.0 does not support while loops",
            f"{indent_str}// Condition: c[{loop.condition.creg}] == {loop.condition.value}"
        ]
        return "\n".join(lines)
    
    def _if_else_to_qasm2(self, if_else: IfElse, indent: int) -> str:
        """Convert if/else to QASM2 conditional statements."""
        indent_str = "  " * indent
        lines = []
        
        # QASM 2.0 if statement: if (c == v) operation;
        condition_str = f"c[{if_else.condition.creg}] == {if_else.condition.value}"
        
        # Single operation in if block (QASM 2.0 limitation)
        if if_else.if_body:
            for op in if_else.if_body:
                qasm_op = self._operation_to_qasm2(op, 0)  # No indent for inner ops
                if qasm_op:
                    lines.append(f"{indent_str}if ({condition_str}) {qasm_op.strip()}")
        
        # Handle else block (not standard in QASM 2.0)
        if if_else.else_body:
            lines.append(f"{indent_str}// else block (not standard in QASM 2.0)")
            for op in if_else.else_body:
                qasm_op = self._operation_to_qasm2(op, indent)
                if qasm_op:
                    lines.append(qasm_op)
        
        return "\n".join(lines)


def circuit_to_qasm2(qc: QuantumCircuit, include_header: bool = True) -> str:
    """
    Convenience function to convert a QuantumCircuit to QASM2.
    
    Args:
        qc: Custom QuantumCircuit IR
        include_header: Whether to include QASM header
        
    Returns:
        OpenQASM 2.0 formatted string
    """
    exporter = QASM2Exporter(include_header=include_header)
    return exporter.export(qc)
