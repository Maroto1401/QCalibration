# normalization.py
import math
from typing import List
from ..core.QuantumCircuit import Operation

PI = math.pi

# ------------------------------------------------
# Canonical normalization basis 
# ------------------------------------------------
NORMALIZATION_BASIS = {
    # single-qubit semantic
    "x", "y", "z",
    "h", "s", "t",
    "rx", "ry", "rz",

    # two-qubit semantic
    "cx", "cz"
}


def is_canonical(op: Operation) -> bool:
    return op.name.lower() in NORMALIZATION_BASIS


def _copy_op(
    name: str,
    qubits,
    params,
    original: Operation,
) -> Operation:
    """Helper to preserve metadata, clbits, and condition."""
    return Operation(
        name=name,
        qubits=qubits,
        clbits=list(original.clbits),
        params=params,
        condition=original.condition,
        metadata=dict(original.metadata),
    )


def normalize_operation(op: Operation) -> List[Operation]:
    name = op.name.lower()
    q = op.qubits
    p = op.params

    # Canonical gates → passthrough
    if is_canonical(op):
        return [op]

    # -------- Parameterized unitaries --------
    if name == "u3":
        if len(p) != 3:
            raise ValueError("U3 gate expects 3 parameters")
        theta, phi, lam = p
        return [
            _copy_op("rz", q, [phi], op),
            _copy_op("rx", q, [theta], op),
            _copy_op("rz", q, [lam], op),
        ]

    # -------- Unsupported --------
    raise NotImplementedError(
        f"Normalization rule not defined for gate: {op.name}"
    )



def normalize_operation_recursive(op: Operation) -> List[Operation]:
    normalized = []
    for new_op in normalize_operation(op):
        if is_canonical(new_op):
            normalized.append(new_op)
        else:
            normalized.extend(normalize_operation_recursive(new_op))
    return normalized
