from fastapi import APIRouter, HTTPException
from ..circuitNormalization.normalization_circuit import normalize_circuit 
from ..core import QuantumCircuit
from .store import parsed_circuits

router = APIRouter(prefix="/normalize", tags=["normalization"]) 

@router.get("/circuit/{circuit_id}")
async def get_normalized_circuit(circuit_id: str):
    qc = parsed_circuits.get(circuit_id)
    if not qc:
        raise HTTPException(status_code=404, detail="Circuit not found")

    try:
        normalized_qc = normalize_circuit(qc)

        # --- Basic info ---
        n_qubits = normalized_qc.num_qubits
        n_clbits = normalized_qc.num_clbits
        n_gates = len(normalized_qc.operations)
        depth = normalized_qc.depth

        # --- Compute additional metrics ---
        n_two_qubit_gates = 0
        n_swap_gates = 0
        n_cx_gates = 0
        two_qubit_gates_dict = {}

        for op in normalized_qc.operations:
            if isinstance(op, QuantumCircuit.Operation):
                if len(op.qubits) == 2:
                    n_two_qubit_gates += 1
                    two_qubit_gates_dict[op.name] = two_qubit_gates_dict.get(op.name, 0) + 1
                if op.name.lower() == "swap":
                    n_swap_gates += 1
                if op.name.lower() == "cx":
                    n_cx_gates += 1

        circuitConnectivity = normalized_qc.get_circuit_connectivity()
        parsed_circuit_connectivity = {
            f"{q1}-{q2}": count
            for (q1, q2), count in circuitConnectivity.items()
        }

        # --- Prepare summary matching original get_circuit ---
        summary = {
            "n_qubits": n_qubits,
            "n_clbits": n_clbits,
            "n_gates": n_gates,
            "gate_names": [op.name for op in normalized_qc.operations],
            "two_qubit_gates": two_qubit_gates_dict,
            "n_two_qubit_gates": n_two_qubit_gates,
            "depth": depth,
            "n_swap_gates": n_swap_gates,
            "n_cx_gates": n_cx_gates,
            "gate_counts": {
                op.name: sum(
                    1 for o in normalized_qc.operations
                    if isinstance(o, QuantumCircuit.Operation) and o.name == op.name
                )
                for op in normalized_qc.operations
                if isinstance(op, QuantumCircuit.Operation)
            },
            "operations": normalized_qc.operations_list(),
            "circuitConnectivity": parsed_circuit_connectivity
        }

        return {"circuit_id": circuit_id, "normalized_summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")
