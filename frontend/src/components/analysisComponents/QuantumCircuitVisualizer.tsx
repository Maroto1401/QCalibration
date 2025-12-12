import { Box, Text, Group, Paper, ScrollArea } from "@mantine/core";
import { CircuitSummary, Operation } from "../../types";
import { Gate } from "./Gate";
import { GATE_SPACING, MARGIN, QUBIT_SPACING } from "../../utils/GATE_CONSTANTS";

interface LayoutGate {
  operation: Operation;
  column: number;
}

interface LayoutResult {
  gates: LayoutGate[];
  numColumns: number;
}

export function calculateLayout(operations: Operation[], numQubits: number): LayoutResult {
  const columns: LayoutGate[] = [];
  const columnOccupied: Set<number>[] = []; // qubits occupied per column

  operations.forEach(op => {
    const qubits = op.qubits;
    // Expand to include all qubits between min and max
    const minQ = Math.min(...qubits);
    const maxQ = Math.max(...qubits);
    const affectedQubits = [];
    for (let q = minQ; q <= maxQ; q++) affectedQubits.push(q);

    let col = 0;
    while (true) {
      if (!columnOccupied[col]) columnOccupied[col] = new Set();

      const conflict = affectedQubits.some(q => columnOccupied[col].has(q));
      if (!conflict) break;
      col++;
    }

    // Place the gate in this column
    columns.push({ operation: op, column: col });

    // Mark qubits as occupied in this column
    affectedQubits.forEach(q => columnOccupied[col].add(q));
  });

  const numColumns = columnOccupied.length;
  return { gates: columns, numColumns: numColumns || 1 };
}


interface QuantumCircuitVisualizerProps {
  circuit: CircuitSummary; 
  maxQubits?: number;
}

export function QuantumCircuitVisualizer({ circuit, maxQubits=40 }: QuantumCircuitVisualizerProps) {
  if (!circuit || circuit.n_qubits === 0) {
    return (
      <Paper p="md" withBorder>
        <Text>No circuit data to display</Text>
      </Paper>
    );
  }
  // Warning for large circuits
  if (circuit.n_qubits > maxQubits) {
    return (
      <Paper p="md" withBorder>
        <Text color="red">
          Circuit has {circuit.n_qubits} qubits, which is too large to visualize. 
          Please reduce the number of qubits under {maxQubits} or use a specialized viewer.
        </Text>
      </Paper>
    );
  }

  const numQubits = circuit.n_qubits;
  const operations: Operation[] = Array.isArray(circuit.operations[0])
  ? (circuit.operations.flat() as Operation[])
  : (circuit.operations as Operation[]);
  const depth = circuit.depth || 0;

  // Convert Operation objects to visual-friendly format (if needed)
  const visualOps = operations.map(op => ({
    type: op.type,
    qubits: op.qubits,
    clbits: op.clbits,
    params: op.params,
  }));
  console.log("Visual operations:", visualOps);

  const layout = calculateLayout(operations, numQubits);

  const width = Math.max(800, layout.numColumns * GATE_SPACING + 2 * MARGIN);
  const height = numQubits * QUBIT_SPACING + MARGIN;

  return (
    <Paper withBorder p="md">
  <Box style={{ display: "flex" }}>
    {/* Left fixed labels */}
    <Box style={{ flexShrink: 0, width: MARGIN, position: "relative", zIndex: 2, background: "white" }}>
      <svg width={MARGIN} height={height}>
        {Array.from({ length: numQubits }).map((_, i) => (
          <g key={`label-${i}`}>
            {/* Qubit line fragment to align with gates */}
            <line
              x1={MARGIN}
              y1={MARGIN + i * QUBIT_SPACING}
              x2={MARGIN}
              y2={MARGIN + i * QUBIT_SPACING}
              stroke="#000"
              strokeWidth={2}
            />
            {/* Qubit label */}
            <Text
              component="text"
              x={MARGIN - 30}
              y={MARGIN + i * QUBIT_SPACING + 5}
              size="sm"
              fill="#000"
            >
              q{i}
            </Text>
          </g>
        ))}
      </svg>
    </Box>

    {/* Scrollable gates */}
    <ScrollArea style={{ width: "100%", overflowX: "auto" }}>
      <Box component="svg" width={width} height={height}>
        {/* Qubit lines */}
        {Array.from({ length: numQubits }).map((_, i) => (
          <line
            key={`line-${i}`}
            x1={MARGIN}
            y1={MARGIN + i * QUBIT_SPACING}
            x2={width - MARGIN}
            y2={MARGIN + i * QUBIT_SPACING}
            stroke="#000"
            strokeWidth={2}
          />
        ))}

        {/* Gates */}
        {layout.gates.map((gate, idx) => (
          <Gate
            key={idx}
            operation={gate.operation}
            x={MARGIN + gate.column * GATE_SPACING}
            y={MARGIN}
            qubitSpacing={QUBIT_SPACING}
          />
        ))}
      </Box>
    </ScrollArea>
  </Box>
</Paper>

  );
}

