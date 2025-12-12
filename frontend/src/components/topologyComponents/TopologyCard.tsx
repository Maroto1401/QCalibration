// TopologyCard.tsx
import { Card, Text, Title, Stack, Badge, Group, ThemeIcon, ScrollArea } from "@mantine/core";
import { IconNetwork } from "@tabler/icons-react";
import { TopologyCard as TopologyCardType } from "../../types";
import { GATE_COLORS } from "../../utils/GATE_CONSTANTS";

interface Props {
  topology: TopologyCardType;
  onSelect?: (id: string) => void;
}

export default function TopologyCard({ topology, onSelect }: Props) {
  const handleClick = () => {
    if (onSelect) onSelect(topology.id);
  };

  const connectivityColor =
  topology.connectivity === "very high"
    ? "blue"
    : topology.connectivity === "high"
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

        {topology.basisGates && topology.basisGates.length > 0 && (
        <Group wrap="wrap">
            <Text size="xs">
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
        {/* Optional description and release date */}
        {topology.description && <Text size="sm">{topology.description}</Text>}
        {topology.releaseDate && <Text size="xs" >Release: {topology.releaseDate}</Text>}

      </Stack>
    </Card>
  );
}
