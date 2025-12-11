import { Text, Group } from "@mantine/core";
import { CircuitSummary } from "../types";

interface CircuitMetricsCirclesProps {
  summary: CircuitSummary;
}

export default function CircuitMetricsCircles({ summary }: CircuitMetricsCirclesProps) {
  const metrics = [
    { label: "Qubits", value: summary.n_qubits, color: "#F6C23E" },
    { label: "Classical Bits", value: summary.n_clbits, color: "#E74A3B" },
    { label: "Total Gates", value: summary.n_gates, color: "#1CC88A" },
    { label: "Depth", value: summary.depth, color: "#36B9CC" },
  ];

  return (
    <div style={{ display: "flex", gap: "16px", justifyContent: "center", width: "100%" }}>
      {metrics.map((metric) => (
        <div key={metric.label} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          {/* Label */}
          <Text size="sm" style={{ marginTop: 6 }}>
            {metric.label}
          </Text>
          {/* Circle */}
          <div
            style={{
              width: 60,
              height: 60,
              borderRadius: "50%",
              backgroundColor: metric.color,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              fontWeight: 700,
              fontSize: 18,
              color: "#fff",
            }}
          >
            {metric.value}
          </div>
        </div>
      ))}
    </div>
  );
}