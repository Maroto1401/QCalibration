// TopologyCard.tsx
import { Card, Text, Title, Stack, Badge, Group, ThemeIcon, ScrollArea } from "@mantine/core";
import { IconNetwork } from "@tabler/icons-react";
import { TopologyCard as TopologyCardType } from "../../types";

interface Props {
  topology: TopologyCardType;
  onSelect?: (id: string) => void;
}

export default function TopologyCard({ topology, onSelect }: Props) {
  const handleClick = () => {
    if (onSelect) onSelect(topology.id);
  };

  const connectivityColor =
    topology.connectivity === "high"
      ? "green"
      : topology.connectivity === "medium"
      ? "yellow"
      : "red";

  return (
    <Card
      shadow="sm"
      padding="lg"
      radius="md"
      withBorder
      style={{ cursor: onSelect ? "pointer" : "default" }}
      onClick={handleClick}
      styles={(theme) => ({
        root: {
          transition: "transform 0.2s, box-shadow 0.2s",
          cursor: onSelect ? "pointer" : "default",
          "&:hover": {
            transform: onSelect ? "scale(1.03)" : "none",
            boxShadow: onSelect ? "0 4px 20px rgba(0,0,0,0.12)" : undefined,
          },
        },
      })}
    >
      <Stack >
        {/* Header */}
        <Group >
          <Group>
            <ThemeIcon size={30} radius="xl" color={connectivityColor} variant="light">
              <IconNetwork size={18} />
            </ThemeIcon>
            <Title order={4}>{topology.name}</Title>
          </Group>
          <Badge color={connectivityColor} variant="light">
            {topology.connectivity.toUpperCase()}
          </Badge>
        </Group>

        {/* Vendor and Qubits */}
        <Text size="sm" >
          Vendor: {topology.vendor}
        </Text>
        <Text size="sm" >
          Qubits: {topology.minQubits} - {topology.maxQubits}
        </Text>

        {/* Optional description and release date */}
        {topology.description && <Text size="sm">{topology.description}</Text>}
        {topology.releaseDate && <Text size="xs" >Release: {topology.releaseDate}</Text>}

        {/* Basis gates */}
        {topology.basisGates && topology.basisGates.length > 0 && (
          <Text size="xs" >
            Basis Gates: {topology.basisGates.join(", ")}
          </Text>
        )}

        {/* Instructions */}
        {topology.instructions && topology.instructions.length > 0 && (
          <ScrollArea style={{ height: 80 }}>
            <Text size="xs" >
              Instructions: {topology.instructions.join(", ")}
            </Text>
          </ScrollArea>
        )}

        {/* Coupling map */}
        {topology.coupling_map && topology.coupling_map.length > 0 && (
          <Text size="xs" >
            Coupling Map: {topology.coupling_map.map(([a, b]) => `[${a}-${b}]`).join(", ")}
          </Text>
        )}

        {/* Calibration data */}
        {topology.calibrationData && (
          <>
            <Text size="xs" >Qubit Calibration:</Text>
            <Text size="xs" >
              {topology.calibrationData.qubits.map(q => 
                `Q${q.qubit}: T1=${q.t1 ?? 'N/A'}, T2=${q.t2 ?? 'N/A'}, Freq=${q.frequency ?? 'N/A'}, ReadoutErr=${q.readout_error ?? 'N/A'}`
              ).join(" | ")}
            </Text>

            <Text size="xs" >Gate Calibration:</Text>
            <Text size="xs" >
              {topology.calibrationData.gates.map(g =>
                `${g.name} [Q${g.qubits.join(",")}]: Error=${g.gate_error ?? 'N/A'}, Duration=${g.duration ?? 'N/A'}`
              ).join(" | ")}
            </Text>
          </>
        )}
      </Stack>
    </Card>
  );
}
