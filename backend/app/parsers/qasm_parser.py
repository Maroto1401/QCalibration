"""
QASM Parser Module

Handles parsing of OpenQASM 2 and OpenQASM 3 quantum circuit descriptions
into a unified circuit representation (UnifiedCircuit). Provides version
detection, AST validation, and conversion to internal circuit format.
"""

from qiskit.qasm2 import loads as qasm2_loads
from qiskit.qasm3 import loads as qasm3_loads
from QuantumCircuit import QuantumCircuit  

class QASMParseError(Exception):
    """Raised when QASM parsing fails (e.g., syntax error, missing version header)."""
    pass


class QASMSemanticError(Exception):
    """Raised when QASM AST is semantically invalid (e.g., out-of-range qubit index)."""
    pass


def parse_qasm(text: str):
    """
    Parses an OpenQASM 2 or 3 file into a UnifiedCircuit object.
    
    This is the main entry point for parsing QASM files. The process consists of:
    1. Detect QASM version from header (OPENQASM 2.0 or OPENQASM 3.0)
    2. Parse text to Abstract Syntax Tree (AST) using Qiskit
    3. Validate AST for semantic errors (e.g., out-of-range qubits)
    4. Convert AST to UnifiedCircuit format (internal representation)
    
    Args:
        text (str): Raw QASM file content as a string
        
    Returns:
        dict: UnifiedCircuit object with keys:
            - num_qubits: Total number of qubits in the circuit
            - gates: List of gate operations (each with name, qubits, params)
            - metadata: Circuit metadata (e.g., source format)
            
    Raises:
        QASMParseError: If version detection or parsing fails
        QASMSemanticError: If AST validation fails
    """
    # 1. Detect version
    version = detect_qasm_version(text)

    # 2. Parse to AST
    ast = qasm_to_ast(text, version)

    # 3. Validate AST
    validate_ast(ast, version)

    # 4. Convert AST → UnifiedCircuit
    circuit = ast_to_unified_circuit(ast)

    return circuit


def detect_qasm_version(text: str) -> int:
    """
    Detects OpenQASM version from the header line.
    
    OpenQASM files must start with a version declaration:
    - OpenQASM 2: "OPENQASM 2.0;"
    - OpenQASM 3: "OPENQASM 3.0;"
    
    Args:
        text (str): Raw QASM content
        
    Returns:
        int: Version number (2 or 3)
        
    Raises:
        QASMParseError: If header is missing or version is unknown
    """
    first_line = text.strip().splitlines()[0]
    # Check for OpenQASM 2.0 header
    if "OPENQASM 2" in first_line:
        return 2
    # Check for OpenQASM 3.0 header
    if "OPENQASM 3" in first_line:
        return 3
    # Neither version found, raise error
    raise QASMParseError("Missing or unknown OPENQASM version header.")


def qasm_to_ast(text: str, version: int):
    """
    Parses QASM text to Abstract Syntax Tree using Qiskit loaders.
    
    Args:
        text (str): Raw QASM content
        version (int): Detected QASM version (2 or 3)
        
    Returns:
        AST object from Qiskit
        
    Raises:
        QASMParseError: If parsing fails (syntax error)
    """
    if version == 2:
        return qasm2_loads(text)
    if version == 3:
        return qasm3_loads(text)
    

def validate_ast(ast, version):
    """
    Validates the Abstract Syntax Tree for semantic errors.
    
    Checks:
    - Circuit has at least 1 qubit (num_qubits > 0)
    - All qubit indices in operations are within valid range [0, num_qubits)
    
    This is a basic validation; more comprehensive checks can be added
    for gate parameters, control flow, etc.
    
    Args:
        ast: Qiskit AST object
        version (int): QASM version (used for version-specific validation)
        
    Raises:
        QASMSemanticError: If validation fails
    """
    # Check that circuit has at least one qubit
    if ast.num_qubits < 1:
        raise QASMSemanticError("Circuit has zero qubits.")

    # Validate each operation's qubit indices
    for op in ast.operations:
        for q in op.qubits:
            # Ensure qubit index is within valid range
            if q.index >= ast.num_qubits:
                raise QASMSemanticError(f"Qubit index {q.index} out of range.")


def ast_to_unified_circuit(ast) -> QuantumCircuit:
    """
    Converts Qiskit AST → QuantumCircuit class.
    """
    circ = QuantumCircuit(num_qubits=len(ast.qubits))
    circ.metadata["source"] = "qasm"

    # Map qubit objects to integer indices
    qubit_map = {q: i for i, q in enumerate(ast.qubits)}

    for instr in ast.operations:
        circ.add_gate(
            name=instr.name,
            qubits=[qubit_map[q] for q in instr.qubits],
            params=instr.params or []
        )

    return circ



