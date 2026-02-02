import { error } from "console";

export interface CircuitSummary {
  n_qubits: number;
  n_clbits: number;
  n_gates: number;
  two_qubit_gates: Record<string, number>;
  n_two_qubit_gates: number;
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
    // Structural metrics
    original_depth: number;
    transpiled_depth: number;
    depth_increase: number;
    total_gates: number;
    n_swap_gates: number;

    // Gate error metrics
    overall_gate_error: number;      // sum of all gate errors
    gate_fidelity: number;           // product of gate fidelities

    // Readout error metrics
    overall_readout_error: number;   // sum of readout errors
    avg_readout_error: number;       // average readout error
    readout_fidelity: number;        // product of readout fidelities

    // Decoherence metrics
    avg_decoherence_error: number;   // average decoherence error across qubits
    decoherence_fidelity: number;    // product of decoherence fidelities

    // Execution time metrics
    overall_execution_time: number;  // total circuit execution time in nanoseconds

    // Final fidelity
    effective_error: number;         // 1 - total_fidelity (combined error from all sources)
    fidelity: number;                // total circuit fidelity (gate × readout × decoherence)

    // Per-qubit detailed metrics (optional)
    per_qubit_metrics?: Record<string, {
      execution_time: number;        // nanoseconds this qubit is active
      t1_error: number;              // T1 decoherence error probability
      t2_error: number;              // T2 decoherence error probability
      decoherence_error: number;     // combined T1+T2 decoherence error
    }>;

    // Legacy/additional metrics (for compatibility)
    gates_inserted?: number;
    n_cx_gates?: number;
    routing_gate_count?: number;
    total_physical_gates?: number;
  };
  summary: CircuitSummary;
  transpiled_qasm2: string;
  normalized_qasm2: string;
  error?: string;                 // optional, if status = 'error'
}