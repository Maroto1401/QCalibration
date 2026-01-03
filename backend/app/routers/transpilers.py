from fastapi import APIRouter, HTTPException
from typing import Dict
from uuid import uuid4
import time

from ..core.BaseModelClasses import TranspilationRequest, TranspilationResult

from ..core.QuantumCircuit import QuantumCircuit, Operation
from .parser_handler import parsed_circuits

router = APIRouter(prefix="/transpile", tags=["transpilation"])

# ==================== HELPER FUNCTIONS ====================

def generate_circuit_summary(qc: QuantumCircuit) -> Dict:
    """Generate summary statistics for a quantum circuit."""
    n_qubits = qc.num_qubits
    n_clbits = qc.num_clbits
    n_gates = len([op for op in qc.operations if isinstance(op, Operation)])
    depth = qc.depth
    
    n_two_qubit_gates = 0
    n_swap_gates = 0
    n_cx_gates = 0
    two_qubit_gates_dict = {}
    gate_counts = {}
    
    for op in qc.operations:
        if isinstance(op, Operation):
            # Count gate types
            gate_counts[op.name] = gate_counts.get(op.name, 0) + 1
            
            # Two-qubit gates
            if len(op.qubits) == 2:
                n_two_qubit_gates += 1
                two_qubit_gates_dict[op.name] = two_qubit_gates_dict.get(op.name, 0) + 1
            
            # Specific gate counts
            if op.name.lower() == "swap":
                n_swap_gates += 1
            if op.name.lower() == "cx":
                n_cx_gates += 1
    
    return {
        "n_qubits": n_qubits,
        "n_clbits": n_clbits,
        "n_gates": n_gates,
        "gate_names": [op.name for op in qc.operations if isinstance(op, Operation)],
        "two_qubit_gates": two_qubit_gates_dict,
        "n_two_qubit_gates": n_two_qubit_gates,
        "depth": depth,
        "n_swap_gates": n_swap_gates,
        "n_cx_gates": n_cx_gates,
        "gate_counts": gate_counts,
        "operations": qc.operations_list()
    }

# ==================== MAIN ENDPOINT ====================

@router.post("/run", response_model=TranspilationResult)
async def run_transpilation(request: TranspilationRequest):
    """
    Run transpilation on a circuit with a specific algorithm.
    Supports: naive, sabre, stochastic, lookahead, basic
    """
    # Get the circuit
    qc = parsed_circuits.get(request.circuit_id)
    if not qc:
        raise HTTPException(status_code=404, detail="Circuit not found")
    
    # Validate topology
    if qc.num_qubits > request.topology.numQubits:
        raise HTTPException(
            status_code=400, 
            detail=f"Circuit requires {qc.num_qubits} qubits but topology only has {request.topology.numQubits}"
        )
    
    # Import algorithm-specific transpilers
    from ..transpilationAlgorithms.naive_transpiler import naive_transpiler
    from ..transpilationAlgorithms.sabre_transpiler import sabre_transpiler
    # from ..transpilationAlgorithms.stochastic_transpiler import stochastic_transpiler
    # from ..transpilationAlgorithms.lookahead_transpiler import lookahead_transpiler
    # from ..transpilationAlgorithms.basic_transpiler import basic_transpiler
    
    start_time = time.time()
    
    # Route to the appropriate algorithm
    algorithm = request.algorithm.lower()
    try:
        if algorithm == "naive":
            transpiled_qc, embedding, metrics = naive_transpiler(qc, request.topology)
        elif algorithm == "sabre":
            transpiled_qc, embedding, metrics = sabre_transpiler(qc, request.topology)
            #raise HTTPException(status_code=501, detail="SABRE algorithm not yet implemented")
            # transpiled_qc, embedding, metrics = sabre_transpiler(qc, request.topology)
        elif algorithm == "stochastic":
            raise HTTPException(status_code=501, detail="Stochastic algorithm not yet implemented")
            # transpiled_qc, embedding, metrics = stochastic_transpiler(qc, request.topology)
        elif algorithm == "lookahead":
            raise HTTPException(status_code=501, detail="Lookahead algorithm not yet implemented")
            # transpiled_qc, embedding, metrics = lookahead_transpiler(qc, request.topology)
        elif algorithm == "basic":
            raise HTTPException(status_code=501, detail="Basic algorithm not yet implemented")
            # transpiled_qc, embedding, metrics = basic_transpiler(qc, request.topology)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {request.algorithm}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transpilation error: {str(e)}")
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    metrics["algorithm_execution_time"] = execution_time
    
    # Store transpiled circuit
    transpiled_circuit_id = str(uuid4())
    parsed_circuits[transpiled_circuit_id] = transpiled_qc
    
    # Generate summary for transpiled circuit
    summary = generate_circuit_summary(transpiled_qc)
    
    return TranspilationResult(
        transpiled_circuit_id=transpiled_circuit_id,
        algorithm=request.algorithm,
        embedding=embedding,
        metrics=metrics,
        summary=summary
    )