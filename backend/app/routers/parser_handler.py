from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from uuid import uuid4

from ..parsers.qasm2_parser import qasm2_parser
from ..parsers.qasm3_parser import qasm3_parser
from ..parsers.json_parser import parse_json
from ..core.QuantumCircuit import QuantumCircuit

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
        elif filename.endswith(".json"):
            filetype = "json"
        else:
            # fallback: try content detection
            first_line = raw_text.strip().split("\n")[0]
            if "OPENQASM 3" in first_line.upper():
                filetype = "qasm3"
            elif "OPENQASM 2" in first_line.upper():
                filetype = "qasm"
            elif raw_text.strip().startswith("{") or raw_text.strip().startswith("["):
                filetype = "json"
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
            elif filetype == "json":
                qc: QuantumCircuit = parse_json(raw_text)
            else:
                raise HTTPException(status_code=500, detail="Unknown filetype detected")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Parser error: {str(e)}")

        # --- Save to backend (memory/DB) ---
        circuit_id = str(uuid4())
        parsed_circuits[circuit_id] = qc

        # --- Return only a reference to the frontend ---
        return {"circuit_id": circuit_id, "message": "Circuit parsed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/circuit/{circuit_id}")
async def get_circuit(circuit_id: str):
    qc = parsed_circuits.get(circuit_id)
    if not qc:
        raise HTTPException(status_code=404, detail="Circuit not found")

    # optionally return metadata/summary only
    summary = {
        "n_qubits": qc.qubit_count,
        "n_clbits": qc.clbit_count,
        "n_gates": len(qc.operations),
        "gate_names": [op.name for op in qc.operations]
    }
    return {"circuit_id": circuit_id, "summary": summary}


