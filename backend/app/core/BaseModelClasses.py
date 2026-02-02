from pydantic import BaseModel
from typing import Dict, List, Optional
# ==================== PYDANTIC MODELS ====================

class QubitCalibration(BaseModel):
    qubit: int
    t1: Optional[float] = None
    t2: Optional[float] = None
    frequency: Optional[float] = None
    readout_error: Optional[float] = None

class GateCalibration(BaseModel):
    name: str
    qubits: List[int]
    gate_error: Optional[float] = None
    duration: Optional[float] = None
    parameters: Dict[str, Optional[float]] = {}

class CalibrationData(BaseModel):
    qubits: List[QubitCalibration]
    gates: List[GateCalibration]

class Topology(BaseModel):
    id: str
    name: str
    vendor: str
    releaseDate: Optional[str] = None
    available: bool
    description: Optional[str] = None
    numQubits: int
    topology_layout: Optional[str] = None  # "heavy-hex" | "grid" | "unknown"
    coupling_map: List[List[int]]  # List of [qubit1, qubit2] pairs
    connectivity: str  # "low" | "medium" | "high" | "very high"
    basisGates: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    calibrationData: Optional[CalibrationData] = None
    iconName: Optional[str] = None

class TranspilationRequest(BaseModel):
    circuit_id: str
    topology: Topology
    algorithm: str  # "naive", "sabre", "stochastic", "lookahead", "basic"



class PerQubitMetric(BaseModel):
    """Per-qubit decoherence and execution metrics"""
    execution_time: float          # nanoseconds this qubit is active
    t1_error: float                # T1 decoherence error probability
    t2_error: float                # T2 decoherence error probability
    decoherence_error: float       # combined T1+T2 decoherence error

class TranspilationMetrics(BaseModel):
    """Comprehensive transpilation metrics including fidelity breakdown"""
    
    # Structural metrics
    original_depth: float
    transpiled_depth: float
    depth_increase: float
    total_gates: float
    n_swap_gates: float

    # Gate error metrics
    overall_gate_error: float      # sum of all gate errors
    gate_fidelity: float           # product of gate fidelities

    # Readout error metrics
    overall_readout_error: float   # sum of readout errors
    avg_readout_error: float       # average readout error
    readout_fidelity: float        # product of readout fidelities

    # Decoherence metrics
    avg_decoherence_error: float   # average decoherence error across qubits
    decoherence_fidelity: float    # product of decoherence fidelities

    # Execution time metrics
    overall_execution_time: float  # total circuit execution time in nanoseconds

    # Final fidelity
    effective_error: float         # 1 - total_fidelity (combined error from all sources)
    fidelity: float                # total circuit fidelity (gate × readout × decoherence)

    # Per-qubit detailed metrics (optional)
    per_qubit_metrics: Optional[Dict[str, PerQubitMetric]] = None

    # Legacy/additional metrics (for compatibility)
    gates_inserted: Optional[float] = None
    n_cx_gates: Optional[float] = None
    routing_gate_count: Optional[float] = None
    total_physical_gates: Optional[float] = None

class TranspilationResult(BaseModel):
    """Complete transpilation result with metrics and circuit summaries"""
    transpiled_circuit_id: str
    algorithm: str
    embedding: Dict[int, int]              # logical_qubit -> physical_qubit mapping
    metrics: TranspilationMetrics
    summary: Dict
    transpiled_qasm2: str
    normalized_qasm2: str