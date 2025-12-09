from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from ..parsers.qasm_parser import parse_qasm
from ..parsers.json_parser import parse_json
from ..core.QuantumCircuit import QuantumCircuit

router = APIRouter(prefix="", tags=["parsing"])


@router.post("/parse-circuit")
async def parse_circuit(file: UploadFile):
    """
    Receives any supported circuit file (.qasm, .qasm3, .json)
    Determines the type and forwards to the correct parser.
    Returns a normalized QuantumCircuit description.
    """
    filename = file.filename.lower()
    raw_text = (await file.read()).decode(errors="ignore")

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
                detail="Unsupported file type. Please upload .qasm, .qasm3 or .json"
            )

    # --- Delegate to the correct parser ---
    try:
        if filetype in ("qasm", "qasm3"):
            qc: QuantumCircuit = parse_qasm(raw_text)
        elif filetype == "json":
            qc: QuantumCircuit = parse_json(raw_text)
        else:
            raise HTTPException(status_code=500, detail="Unknown filetype detected")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parser error: {str(e)}")

    # --- Return the unified circuit representation ---
    return JSONResponse(content={"circuit": qc.to_dict()})
