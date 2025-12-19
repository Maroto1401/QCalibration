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

class TranspilationResult(BaseModel):
    transpiled_circuit_id: str
    algorithm: str
    embedding: Dict[int, int]  # logical_qubit -> physical_qubit mapping
    metrics: Dict[str, float]
    summary: Dict