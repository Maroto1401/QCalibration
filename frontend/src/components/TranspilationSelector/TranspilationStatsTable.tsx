import { Card, Grid, Title, Text } from "@mantine/core";
import { CircuitSummary, TranspilationResult } from "../../types";

export const TranspilationStatsTable: React.FC<{
  result: TranspilationResult;
  originalCircuit: CircuitSummary;
  normalizedCircuit: CircuitSummary;
  transpilledCircuit: CircuitSummary;
}> = ({ result, originalCircuit, normalizedCircuit, transpilledCircuit }) => {
  if (!result.metrics || !transpilledCircuit) return null;

  // ---- helpers ----
  const pct = (delta: number, base: number) =>
    base === 0 ? "—" : `${((delta / base) * 100).toFixed(1)}%`;

  const deltaLabel = (value: number, base: number) => {
    const d = value - base;
    if (d === 0) return null;
    return `${d > 0 ? "+" : ""}${d} (${pct(d, base)})`;
  };

  // Approximate SWAP gates if not explicitly present
  const nSwapTranspiled =
    result.metrics.n_swap_gates ??
    0;

  // ---- comparison rows ----
  const comparisonData = [
    {
      metric: "Total Gates",
      original: originalCircuit.n_gates,
      normalized: normalizedCircuit.n_gates,
      transpiled: transpilledCircuit.n_gates,
    },
    {
      metric: "Two-Qubit Gates",
      original: originalCircuit.n_two_qubit_gates,
      normalized: normalizedCircuit.n_two_qubit_gates,
      transpiled: transpilledCircuit.n_two_qubit_gates,
    },
    {
      metric: "Circuit Depth",
      original: originalCircuit.depth,
      normalized: normalizedCircuit.depth,
      transpiled: transpilledCircuit.depth,
    },
    {
      metric: "SWAP Gates",
      original: originalCircuit.n_swap_gates ?? 0,
      normalized: normalizedCircuit.n_swap_gates ?? 0,
      transpiled: nSwapTranspiled,
    },
  ];

  return (
    <Card withBorder p="lg">
      <Title order={4} mb="md">
        Circuit Comparison
      </Title>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #dee2e6" }}>
              <th style={{ padding: 12, textAlign: "left" }}>Metric</th>
              <th style={{ padding: 12, textAlign: "center" }}>Original</th>
              <th style={{ padding: 12, textAlign: "center" }}>Normalized</th>
              <th style={{ padding: 12, textAlign: "center" }}>Transpiled</th>
            </tr>
          </thead>

          <tbody>
            {comparisonData.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: "1px solid #f1f3f5" }}>
                {/* Metric */}
                <td style={{ padding: 12, fontWeight: 500 }}>
                  {row.metric}
                </td>

                {/* Original */}
                <td style={{ padding: 12, textAlign: "center" }}>
                  {row.original}
                </td>

                {/* Normalized (Δ vs Original) */}
                <td style={{ padding: 12, textAlign: "center" }}>
                  <div>{row.normalized}</div>
                  {row.normalized !== row.original && (
                    <Text size="xs" c="dimmed">
                      {deltaLabel(row.normalized, row.original)}
                    </Text>
                  )}
                </td>

                {/* Transpiled (Δ vs Normalized) */}
                <td style={{ padding: 12, textAlign: "center" }}>
                  <div>{row.transpiled}</div>
                  {row.transpiled !== row.normalized && (
                    <Text
                      size="xs"
                      fw={600}
                      c={row.transpiled > row.normalized ? "red" : "green"}
                    >
                      {deltaLabel(row.transpiled, row.normalized)}
                    </Text>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ---- metrics cards (unchanged) ---- */}
      <Grid mt="lg">
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="red.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Gate Error
            </Text>
            <Text size="xl" fw={700} c="red">
              {(result.metrics.gate_error * 100).toFixed(3)}%
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="orange.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Decoherence Risk
            </Text>
            <Text size="xl" fw={700} c="orange">
              {(result.metrics.decoherence_risk * 100).toFixed(2)}%
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="blue.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Readout Error
            </Text>
            <Text size="xl" fw={700} c="blue">
              {(result.metrics.readout_error * 100).toFixed(2)}%
            </Text>
          </Card>
        </Grid.Col>
      </Grid>

      <Grid mt="md">
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="violet.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Effective Error
            </Text>
            <Text size="xl" fw={700} c="violet">
              {(result.metrics.effective_error * 100).toFixed(2)}%
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="green.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Fidelity
            </Text>
            <Text size="xl" fw={700} c="green">
              {(result.metrics.fidelity * 100).toFixed(2)}%
            </Text>
          </Card>
        </Grid.Col>

        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="blue.0">
            <Text size="xs" c="dimmed" tt="uppercase">
              Execution Time
            </Text>
            <Text size="xl" fw={700} c="blue">
              {(result.metrics.execution_time * 1e6).toFixed(2)} μs
            </Text>
          </Card>
        </Grid.Col>
      </Grid>
    </Card>
  );
};
