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
