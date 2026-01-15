from fastapi import APIRouter, HTTPException, Query
from ..circuitNormalization import internal_normalization_circuit, basis_mapping
from ..core import QuantumCircuit
from .store import parsed_circuits
from typing import List, Optional

router = APIRouter(prefix="/normalize", tags=["normalization"]) 

@router.get("/circuit/{circuit_id}")
async def get_normalized_circuit(
    circuit_id: str,
    target_basis: Optional[List[str]] = Query(None)
):
    """
    Normalize a circuit to canonical IR and then map to a target basis.
    target_basis: list of gate names as query parameters.
    """
    print(f"[DEBUG] Requested normalized circuit: {circuit_id} with target_basis={target_basis}")
    qc = parsed_circuits.get(circuit_id)
    if not qc:
        print(f"[DEBUG] Circuit ID {circuit_id} not found in store")
        raise HTTPException(status_code=404, detail="Circuit not found")

    print(f"[DEBUG] Found circuit with {qc.num_qubits} qubits and {len(qc.operations)} operations")

    try:
        # Step 1: normalize to canonical IR
        normalized_qc = internal_normalization_circuit.normalize_circuit(qc)
        print(f"[DEBUG] Canonical normalization produced {len(normalized_qc.operations)} operations")

        # Step 2: map to target basis
        mapped_qc = basis_mapping.map_to_basis(normalized_qc, [g.lower() for g in target_basis])
        print(f"[DEBUG] Mapping to target basis produced {len(mapped_qc.operations)} operations")

        # Step 3: prepare summary
        n_qubits = mapped_qc.num_qubits
        n_clbits = mapped_qc.num_clbits
        n_gates = len(mapped_qc.operations)
        depth = mapped_qc.depth

        n_two_qubit_gates = 0
        n_swap_gates = 0
        n_cx_gates = 0
        two_qubit_gates_dict = {}

        for i, op in enumerate(mapped_qc.operations):
            print(f"[DEBUG] Operation {i}: {op}")
            if isinstance(op, QuantumCircuit.Operation):
                if len(op.qubits) == 2:
                    n_two_qubit_gates += 1
                    two_qubit_gates_dict[op.name] = two_qubit_gates_dict.get(op.name, 0) + 1
                if op.name.lower() == "swap":
                    n_swap_gates += 1
                if op.name.lower() == "cx":
                    n_cx_gates += 1

        circuitConnectivity = mapped_qc.get_circuit_connectivity()
        parsed_circuit_connectivity = {f"{q1}-{q2}": count for (q1, q2), count in circuitConnectivity.items()}

        summary = {
            "n_qubits": n_qubits,
            "n_clbits": n_clbits,
            "n_gates": n_gates,
            "gate_names": [op.name for op in mapped_qc.operations],
            "two_qubit_gates": two_qubit_gates_dict,
            "n_two_qubit_gates": n_two_qubit_gates,
            "depth": depth,
            "n_swap_gates": n_swap_gates,
            "n_cx_gates": n_cx_gates,
            "gate_counts": {
                op.name: sum(
                    1 for o in mapped_qc.operations
                    if isinstance(o, QuantumCircuit.Operation) and o.name == op.name
                )
                for op in mapped_qc.operations
                if isinstance(op, QuantumCircuit.Operation)
            },
            "operations": mapped_qc.operations_list(),
            "circuitConnectivity": parsed_circuit_connectivity
        }

        print(f"[DEBUG] Summary prepared successfully")
        return {"circuit_id": circuit_id, "normalized_summary": summary}

    except Exception as e:
        print(f"[ERROR] Normalization/mapping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Normalization/mapping failed: {str(e)}")
