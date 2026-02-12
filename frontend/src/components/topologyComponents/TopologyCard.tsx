// Topology card - displays individual quantum hardware topology with key metrics
import { Card, Text, Title, Stack, Badge, Group, ThemeIcon, Button } from "@mantine/core";
import { IconNetwork } from "@tabler/icons-react";
import { CircuitData, Topology } from "../../types";
import { GATE_COLORS } from "../../utils/GATE_CONSTANTS";
import { useNavigate } from "react-router-dom";
import { getConnectivityMeta } from "../../utils/functions";

interface Props {
  topology: Topology;
  circuit: CircuitData;
  onSelect?: (id: string) => void;
}

export default function TopologyCard({ topology, circuit, onSelect }: Props) {
  const navigate = useNavigate();
  
  const handlePreview = (e: React.MouseEvent) => {
  e.stopPropagation();
  navigate("/topology/preview", {
    state: { topology, circuit },
  });
};


  const connectivity = getConnectivityMeta(topology.connectivity);


  return (
    <Card
      shadow="sm"
      padding="lg"
      radius="md"
      withBorder
      style={{ cursor: onSelect ? "pointer" : "default" }}
      // onClick={handleClick} Uncomment to add a click handler on the Card
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
            <ThemeIcon size={30} radius="xl" color={connectivity.color} variant="light">
              <IconNetwork size={18} />
            </ThemeIcon>
            <Title order={4}>{topology.name}</Title>
          </Group>
          <Badge
            variant="light"
            color={connectivity.color}
            >
            {connectivity.label}
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
        {topology.releaseDate && (
          <Group
    style={{
      display: "flex",
      justifyContent: "space-between",
    }}
  >
            <Text size="xs">Release: {topology.releaseDate}</Text>
            <Button size="xs" variant="light" onClick={handlePreview}>
              Preview
            </Button>
          </Group>
        )}

      </Stack>
    </Card>
  );
}
