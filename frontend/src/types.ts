export interface CircuitSummary {
  n_qubits: number;
  n_clbits: number;
  n_gates: number;
  two_qubit_gates: Record<string, number>;
  n_two_qubit_gates: number;
  n_cx_gates: number;
  n_swap_gates: number;
  depth: number;
  gate_counts: Record<string, number>;
  operations: Operation[];
  circuitConnectivity: Record<string, number>;
}
export interface Operation {
  type: string;
  qubits: number[];
  clbits?: number[];
  params?: number[];
}

export interface CircuitData {
  circuit_id: string;
  summary: CircuitSummary;
}

export interface CircuitMetadata {
  filename: string;
  filetype: string;
  circuit_id: string;
}

// types.ts
export interface QubitCalibration {
  qubit: number;
  t1: number | null;
  t2: number | null;
  frequency: number | null;
  readout_error: number | null;
}

export interface GateCalibration {
  name: string;
  qubits: number[];
  gate_error: number | null;
  duration: number | null;
  parameters: Record<string, number | null>; // converted from backend parameter objects
}

export interface CalibrationData {
  qubits: QubitCalibration[];
  gates: GateCalibration[];
}

export interface Topology {
  id: string;
  name: string;
  vendor: string;
  releaseDate?: string;
  available: boolean;
  description?: string;

  numQubits: number;
  topology_layout?: "heavy-hex" | "grid" | "unknown";
  coupling_map: [number, number][];
  connectivity: "low" | "medium" | "high" | "very high";

  basisGates?: string[];
  instructions?: string[];   // backend.instructions is just names

  calibrationData?: CalibrationData;

  iconName?: string;
}

export interface TranspilationResult {
  transpiled_circuit_id: string;
  algorithm: string;
  embedding: Record<number, number>;
  metrics: {
    execution_time: number;       // total duration in ms
    gate_error: number;           // accumulated gate error
    decoherence_risk: number;     // risk based on T1/T2 and execution time
    readout_error: number;        // expected measurement error
    effective_error: number;      // total effective error
    fidelity: number;             // expected circuit fidelity
    gates_inserted: number;
    depth_increase: number;
    n_swap_gates: number;
    n_cx_gates: number;
    total_gates: number;
    original_depth: number;
    transpiled_depth: number;
  };
  summary: CircuitSummary;
  error?: string;                 // optional, if status = 'error'
}
