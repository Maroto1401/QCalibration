// Topology header - displays topology name, vendor, and key properties
import {
  Group,
  Stack,
  Title,
  Text,
  Badge,
  Avatar,
} from "@mantine/core";
import {
  IconCircuitResistor,
  IconCpu,
  IconCheck,
  IconX,
} from "@tabler/icons-react";
import { Topology } from "../../types";
import { GATE_COLORS } from "../../utils/GATE_CONSTANTS";
import { getConnectivityMeta } from "../../utils/functions";


interface Props {
  topology: Topology;
}

export function TopologyHeader({ topology }: Props) {
  const availabilityColor = topology.available ? "green" : "red";
  const connectivity = getConnectivityMeta(topology.connectivity);


  return (
    <Stack gap="md">
      {/* Top row: logo + title */}
      <Group align="center" gap="md">
        {/* Vendor logo placeholder */}
        <Avatar
          size={56}
          radius="md"
          color="blue"
          variant="light"
        >
          <IconCircuitResistor size={28} />
        </Avatar>

        <Stack gap={4}>
          <Title
            order={2}
            fw={700}
            style={{
              background:
                "linear-gradient(45deg, #228BE6 0%, #15AABF 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            {topology.name}
          </Title>

          <Text size="sm" c="dimmed">
            Vendor: {topology.vendor}
          </Text>
        </Stack>
      </Group>

      {/* Metadata row */}
      <Group gap="sm" wrap="wrap">

        <Badge
          leftSection={
            topology.available ? (
              <IconCheck size={12} />
            ) : (
              <IconX size={12} />
            )
          }
          variant="light"
          color={availabilityColor}
        >
          {topology.available ? "Available" : "Unavailable"}
        </Badge>
        <Badge
          leftSection={<IconCpu size={12} />}
          variant="light"
          color="blue"
        >
          {topology.numQubits} qubits
        </Badge>

        <Badge
        variant="light"
        color={connectivity.color}
        >
        Connectivity: {connectivity.label}
        </Badge>

        {topology.releaseDate && (
          <Badge variant="light" color="gray">
            Released: {topology.releaseDate}
          </Badge>
        )}
      </Group>

      {/* Basis gates */}
{topology.basisGates && topology.basisGates.length > 0 && (
  <Group
    align="flex-start"
    gap="sm"
    wrap="wrap"
  >
    <Text size="sm" fw={600} c="dimmed">
      Basis gates
    </Text>

    <Group gap="xs" wrap="wrap">
      {topology.basisGates.map((gate) => (
        <Badge
          key={gate}
          size="sm"
          variant="light"
          color={GATE_COLORS[gate] || "gray"}
        >
          {gate.toUpperCase()}
        </Badge>
      ))}
    </Group>
  </Group>
)}

    </Stack>
  );
}
