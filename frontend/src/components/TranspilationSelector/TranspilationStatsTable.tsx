import { Card, Grid, Title, Text } from "@mantine/core";
import { TranspilationResult } from "../../types";

export const TranspilationStatsTable: React.FC<{
  result: TranspilationResult;
  originalCircuit: any;
}> = ({ result, originalCircuit }) => {
  if (!result.metrics || !result.summary) return null;

  // Approximate SWAP gates if not provided
  const nSwapTranspiled = result.summary.n_swap_gates ?? Math.round(
    (result.summary.n_cx_gates - originalCircuit.n_cx_gates) / 3
  );

  const comparisonData = [
    { 
      metric: 'Total Gates', 
      original: originalCircuit.n_gates, 
      transpiled: result.summary.n_gates,
      change: result.summary.n_gates - originalCircuit.n_gates
    },
    { 
      metric: 'Two-Qubit Gates', 
      original: originalCircuit.n_two_qubit_gates, 
      transpiled: result.summary.n_two_qubit_gates,
      change: result.summary.n_two_qubit_gates - originalCircuit.n_two_qubit_gates
    },
    { 
      metric: 'Circuit Depth', 
      original: originalCircuit.depth, 
      transpiled: result.summary.depth,
      change: result.metrics.depth_increase
    },
    { 
      metric: 'CX Gates', 
      original: originalCircuit.n_cx_gates, 
      transpiled: result.summary.n_cx_gates,
      change: result.summary.n_cx_gates - originalCircuit.n_cx_gates
    },
    { 
      metric: 'SWAP Gates', 
      original: originalCircuit.n_swap_gates, 
      transpiled: nSwapTranspiled,
      change: nSwapTranspiled - originalCircuit.n_swap_gates
    },
  ];

  return (
    <Card withBorder p="lg">
      <Title order={4} mb="md">Circuit Comparison Table</Title>
      
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #dee2e6' }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600 }}>Metric</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600 }}>Original</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600 }}>Transpiled</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600 }}>Change</th>
            </tr>
          </thead>
          <tbody>
            {comparisonData.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f3f5' }}>
                <td style={{ padding: '12px', fontWeight: 500 }}>{row.metric}</td>
                <td style={{ padding: '12px', textAlign: 'right' }}>{row.original}</td>
                <td style={{ padding: '12px', textAlign: 'right' }}>{row.transpiled}</td>
                <td style={{ 
                  padding: '12px', 
                  textAlign: 'right',
                  color: row.change > 0 ? '#fa5252' : row.change < 0 ? '#51cf66' : '#868e96',
                  fontWeight: 600
                }}>
                  {row.change > 0 ? '+' : ''}{row.change}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <Grid mt="lg">
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="red.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Gate Error</Text>
            <Text size="xl" fw={700} c="red">{(result.metrics.gate_error * 100).toFixed(3)}%</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="orange.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Decoherence Risk</Text>
            <Text size="xl" fw={700} c="orange">{(result.metrics.decoherence_risk * 100).toFixed(2)}%</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="blue.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Readout Error</Text>
            <Text size="xl" fw={700} c="blue">{(result.metrics.readout_error * 100).toFixed(2)}%</Text>
          </Card>
        </Grid.Col>
      </Grid>

      <Grid mt="md">
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="violet.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Effective Error</Text>
            <Text size="xl" fw={700} c="violet">{(result.metrics.effective_error * 100).toFixed(2)}%</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="green.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Fidelity</Text>
            <Text size="xl" fw={700} c="green">{(result.metrics.fidelity * 100).toFixed(2)}%</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card padding="sm" withBorder bg="blue.0">
            <Text size="xs" c="dimmed" tt="uppercase" mb={4}>Execution Time</Text>
            <Text size="xl" fw={700} c="blue">{(result.metrics.execution_time * 1e6).toFixed(2)} μs</Text>
          </Card>
        </Grid.Col>
      </Grid>
    </Card>
  );
};
