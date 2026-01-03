from fastapi import APIRouter, UploadFile, HTTPException
from uuid import uuid4

from ..parsers.qasm2_parser import qasm2_parser
from ..parsers.qasm3_parser import qasm3_parser
from ..core.QuantumCircuit import QuantumCircuit, Operation

router = APIRouter(prefix="", tags=["parsing"])
parsed_circuits = {}  # simple in-memory store; replace with DB in prod

@router.post("/parse-circuit")
async def parse_circuit(file: UploadFile):
    """
    Receives any supported circuit file (.qasm, .qasm3, .json)
    Determines the type and forwards to the correct parser.
    Returns a normalized QuantumCircuit description.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")

        filename = file.filename.lower()
        file_content = await file.read()
        raw_text = file_content.decode(errors="ignore")

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="File is empty")

        # --- Detect type by extension ---
        if filename.endswith(".qasm3"):
            filetype = "qasm3"
        elif filename.endswith(".qasm"):
            filetype = "qasm"
        else:
            # fallback: try content detection
            first_line = raw_text.strip().split("\n")[0]
            if "OPENQASM 3" in first_line.upper():
                filetype = "qasm3"
            elif "OPENQASM 2" in first_line.upper():
                filetype = "qasm"
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type. Filename: {filename}. First line: {first_line[:100]}"
                )

        # --- Delegate to the correct parser ---
        try:
            if filetype == "qasm":
                qc: QuantumCircuit = qasm2_parser(raw_text)
            elif filetype == "qasm3":
                qc: QuantumCircuit = qasm3_parser(raw_text)
            else:
                raise HTTPException(status_code=500, detail="Unknown filetype detected")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Parser error: {str(e)}")

        # --- Save to backend (memory/DB) ---
        circuit_id = str(uuid4())
        parsed_circuits[circuit_id] = qc

        # --- Return only a reference to the frontend ---
        return {"circuit_id": circuit_id, "message": "Circuit parsed successfully", "filename":filename, "filetype": filetype}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/circuit/{circuit_id}")
async def get_circuit(circuit_id: str):
    qc = parsed_circuits.get(circuit_id)
    if not qc:
        raise HTTPException(status_code=404, detail="Circuit not found")

    # --- Basic info ---
    n_qubits = qc.num_qubits
    n_clbits = qc.num_clbits
    n_gates = len(qc.operations)
    depth = qc.depth
    # --- Compute additional metrics ---
    n_two_qubit_gates = 0
    n_swap_gates = 0
    n_cx_gates = 0
    two_qubit_gates_dict = {}

    for op in qc.operations:
        # Only count actual Operation instances, not control flow
        if isinstance(op, Operation):
            if len(op.qubits) == 2:
                n_two_qubit_gates += 1
                two_qubit_gates_dict[op.name] = two_qubit_gates_dict.get(op.name, 0) + 1
            if op.name.lower() == "swap":
                n_swap_gates += 1
            if op.name.lower() == "cx":
                n_cx_gates += 1
    circuitConnectivity = qc.get_circuit_connectivity()
    parsed_circuit_connectivity = {
    f"{q1}-{q2}": count
    for (q1, q2), count in circuitConnectivity.items()
}
    # --- Prepare summary ---
    summary = {
        "n_qubits": n_qubits,
        "n_clbits": n_clbits,
        "n_gates": n_gates,
        "gate_names": [op.name for op in qc.operations],
        "two_qubit_gates": two_qubit_gates_dict,
        "n_two_qubit_gates": n_two_qubit_gates,
        "depth": depth,
        "n_swap_gates": n_swap_gates,
        "n_cx_gates": n_cx_gates, 
        "gate_counts": {op.name: sum(1 for o in qc.operations if isinstance(o, Operation) and o.name == op.name) for op in qc.operations if isinstance(op, Operation)},
        "operations": qc.operations_list(),
        "circuitConnectivity": parsed_circuit_connectivity
    }
    return {"circuit_id": circuit_id, "summary": summary}



