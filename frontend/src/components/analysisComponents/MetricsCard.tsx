import { Text, Group, Stack } from "@mantine/core";
import { CircuitSummary } from "../../types";

interface CircuitMetricsCirclesProps {
  summary: CircuitSummary;
}

export default function CircuitMetricsCircles({ summary }: CircuitMetricsCirclesProps) {
  const metrics = [
    { label: "Qubits", value: summary.n_qubits, color: "#F6C23E" },
    { label: "Total Gates", value: summary.n_gates, color: "#1CC88A" },
    { label: "Depth", value: summary.depth, color: "#36B9CC" },
    { label: "Classical Bits", value: summary.n_clbits, color: "#E74A3B" }
  ];

  return (
    <Group justify="center" gap="md" style={{ width: "100%" }}>
  {metrics.map((metric) => (
    <Stack key={metric.label} align="center" gap="xs">
      {/* Label */}
      <Text size="sm">
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
    </Stack>
  ))}
</Group>
  );
}