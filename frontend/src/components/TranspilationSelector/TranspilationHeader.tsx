import { Badge, Grid, Group, Paper, Stack, Title, Text } from "@mantine/core";
import { CircuitData, Topology} from "../../types";
import { IconCircuitSwitchOpen, IconCpu } from "@tabler/icons-react";
import { GATE_COLORS } from "../../utils/GATE_CONSTANTS";

export const TranspilationHeader: React.FC<{
  circuit: CircuitData;
  topology: Topology;
}> = ({ circuit, topology }) => {
  return (
    <Paper p="lg" mb="md" withBorder>
      <Grid>
        <Grid.Col span={6}>
          <Group mb="xs">
            <IconCircuitSwitchOpen size={24} />
            <Title order={3}>Quantum Circuit</Title>
          </Group>
          <Stack gap="xs">
            <Group gap="md">
              <Badge variant="light" color="blue">ID: {circuit.circuit_id}</Badge>
              <Badge variant="light">{circuit.summary.n_qubits} Qubits</Badge>
              <Badge variant="light">{circuit.summary.n_clbits} Classical Bits</Badge>
            </Group>
            <Group gap="md">
              <Text size="sm" c="dimmed">Gates: {circuit.summary.n_gates}</Text>
              <Text size="sm" c="dimmed">2Q Gates: {circuit.summary.n_two_qubit_gates}</Text>
              <Text size="sm" c="dimmed">Depth: {circuit.summary.depth}</Text>
            </Group>
          </Stack>
        </Grid.Col>
        
        <Grid.Col span={6}>
          <Group mb="xs">
            <IconCpu size={24} />
            <Title order={3}>Hardware Topology</Title>
          </Group>
          <Stack gap="xs">
            <Group gap="md">
              <Badge variant="light" color="violet">{topology.name}</Badge>
              <Badge variant="light" color="grape">{topology.vendor}</Badge>
              <Badge variant={topology.available ? "light" : "outline"} 
                     color={topology.available ? "green" : "gray"}>
                {topology.available ? "Available" : "Unavailable"}
              </Badge>
            </Group>
            <Group justify="space-between" align="flex-start" gap="md">
          <Group gap="md">
            <Text size="sm" c="dimmed">
              {topology.numQubits} Qubits
            </Text>
            <Text size="sm" c="dimmed">
              Connectivity: {topology.connectivity}
            </Text>
            <Text size="sm" c="dimmed">
              Layout: {topology.topology_layout || "unknown"}
            </Text>
          </Group>

          {/* Right side basis gates */}
          {topology.basisGates && topology.basisGates.length > 0 && (
            <Group gap="xs" wrap="wrap">
              <Text size="xs" c="dimmed">
                Basis Gates:
              </Text>
              {topology.basisGates.map((g) => (
                <Badge
                  key={g}
                  color={GATE_COLORS[g] || "gray"}
                  variant="light"
                  size="xs"
                >
                  {g.toUpperCase()}
                </Badge>
              ))}
            </Group>
          )}
        </Group>

            
          </Stack>
        </Grid.Col>
      </Grid>
    </Paper>
  );
};