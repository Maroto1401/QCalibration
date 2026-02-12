// Gate - renders individual quantum gate in circuit visualization
import { Operation } from "../../types";
import { GATE_COLORS } from "../../utils/GATE_CONSTANTS";

interface GateProps {
  operation: Operation;
  x: number;
  y: number;
  qubitSpacing: number;
}

export function Gate({ operation, x, y, qubitSpacing }: GateProps) {
  const gateColor = GATE_COLORS[operation.type] || "#3B82F6"; // Blue default instead of grey

  // Single-qubit gate
  if (operation.qubits.length === 1) {
    const qubitY = y + operation.qubits[0] * qubitSpacing;
    
    if (operation.type === "barrier") {
      return (
        <line
          x1={x}
          y1={qubitY - 30}
          x2={x}
          y2={qubitY + 30}
          stroke="#95A5A6"
          strokeWidth={3}
          strokeDasharray="5,5"
        />
      );
    }

    if (operation.type === "measure") {
      return (
        <g>
          <rect x={x - 32} y={qubitY - 22} width={64} height={44} fill="white" stroke="none" />
          <rect x={x - 30} y={qubitY - 20} width={60} height={40} fill={gateColor} stroke="#000" strokeWidth={2} rx={4} />
          <path d={`M ${x - 15} ${qubitY + 5} Q ${x} ${qubitY - 10}, ${x + 15} ${qubitY + 5}`} fill="none" stroke="white" strokeWidth={2} />
          <line x1={x + 10} y1={qubitY + 5} x2={x + 15} y2={qubitY - 5} stroke="white" strokeWidth={2} />
        </g>
      );
    }

    const displayName = operation.type.toUpperCase();
    const hasParams = operation.params && operation.params.length > 0;

    return (
      <g>
        <rect x={x - 32} y={qubitY - 22} width={64} height={44} fill="white" stroke="none" />
        <rect x={x - 30} y={qubitY - 20} width={60} height={40} fill={gateColor} stroke="#000" strokeWidth={2} rx={4} />
        <text x={x} y={qubitY + 5} textAnchor="middle" fontSize={16} fontWeight="bold" fill="white">
          {displayName}
        </text>
        {hasParams && (
          <text x={x} y={qubitY + 30} textAnchor="middle" fontSize={10} fill="#666">
            θ={operation.params![0].toFixed(2)}
          </text>
        )}
      </g>
    );
  }

  // Two-qubit gate (CX, CZ, SWAP)
  if (operation.qubits.length === 2) {
    const [q1, q2] = operation.qubits;
    const y1 = y + q1 * qubitSpacing;
    const y2 = y + q2 * qubitSpacing;
    const minY = Math.min(y1, y2);
    const maxY = Math.max(y1, y2);

    if (operation.type === "cx" || operation.type === "cnot") {
      return (
        <g>
          <line x1={x} y1={minY} x2={x} y2={maxY} stroke="#000" strokeWidth={2} />
          <circle cx={x} cy={y1} r={10} fill="white" stroke="none" />
          <circle cx={x} cy={y1} r={8} fill="#000" />
          <circle cx={x} cy={y2} r={22} fill="white" stroke="none" />
          <circle cx={x} cy={y2} r={20} fill="none" stroke="#000" strokeWidth={2} />
          <line x1={x - 12} y1={y2} x2={x + 12} y2={y2} stroke="#000" strokeWidth={2} />
          <line x1={x} y1={y2 - 12} x2={x} y2={y2 + 12} stroke="#000" strokeWidth={2} />
        </g>
      );
    }

    if (operation.type === "swap") {
      return (
        <g>
          <line x1={x} y1={minY} x2={x} y2={maxY} stroke="#000" strokeWidth={2} />
          {[y1, y2].map((qy, i) => (
            <g key={i}>
              <rect x={x - 15} y={qy - 15} width={30} height={30} fill="white" stroke="none" />
              <line x1={x - 10} y1={qy - 10} x2={x + 10} y2={qy + 10} stroke="#000" strokeWidth={2} />
              <line x1={x - 10} y1={qy + 10} x2={x + 10} y2={qy - 10} stroke="#000" strokeWidth={2} />
            </g>
          ))}
        </g>
      );
    }

    // Generic two-qubit gate - add qubit numbers inside
    return (
      <g>
        <rect x={x - 32} y={minY - 22} width={64} height={maxY - minY + 44} fill="white" stroke="none" />
        <rect x={x - 30} y={minY - 20} width={60} height={maxY - minY + 40} fill={gateColor} fillOpacity={0.8} stroke="#000" strokeWidth={2} rx={4} />
        <text x={x} y={(y1 + y2) / 2 + 5} textAnchor="middle" fontSize={14} fontWeight="bold" fill="white">
          {operation.type.toUpperCase()}
        </text>
        {[y1, y2].map((qy, i) => {
          const qubitIdx = operation.qubits[i];
          return (
            <text key={`qubit-${qubitIdx}`} x={x} y={qy + 5} textAnchor="middle" fontSize={10} fontWeight="bold" fill="white">
              q{qubitIdx}
            </text>
          );
        })}
      </g>
    );
  }

  // Multi-qubit gate (3+ qubits)
  if (operation.qubits.length >= 3) {
    const qubitsY = operation.qubits.map(q => y + q * qubitSpacing);
    const minY = Math.min(...qubitsY);
    const maxY = Math.max(...qubitsY);

    return (
      <g>
        <rect x={x - 32} y={minY - 22} width={64} height={maxY - minY + 44} fill="white" stroke="none" />
        <rect x={x - 30} y={minY - 20} width={60} height={maxY - minY + 40} fill={gateColor} fillOpacity={0.8} stroke="#000" strokeWidth={2} rx={4} />
        <text x={x} y={(minY + maxY) / 2 + 5} textAnchor="middle" fontSize={14} fontWeight="bold" fill="white">
          {operation.type.toUpperCase()}
        </text>
        {operation.qubits.map((qubitIdx) => {
          const qubitY = y + qubitIdx * qubitSpacing;
          return (
            <text key={`qubit-${qubitIdx}`} x={x} y={qubitY + 5} textAnchor="middle" fontSize={10} fontWeight="bold" fill="white">
              q{qubitIdx}
            </text>
          );
        })}
      </g>
    );
  }

  return null;
}
