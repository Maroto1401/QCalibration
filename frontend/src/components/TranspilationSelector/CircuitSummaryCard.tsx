// Circuit summary card - displays uploaded circuit metadata and properties
import { Card, Text, Title, Stack, Badge, Group, ThemeIcon, Button } from "@mantine/core";
import { IconNetwork } from "@tabler/icons-react"; 
import { CircuitData, CircuitMetadata } from "../../types";
import { useNavigate } from "react-router-dom";

interface Props {
  circuit: CircuitData;
  metadata?: CircuitMetadata;
  onSelect?: (id: string) => void;
}

export default function CircuitCard({ circuit, metadata, onSelect }: Props) {
  const navigate = useNavigate();
  const summary = circuit.summary;

  const handleClick = () => {
    if (onSelect) onSelect(circuit.circuit_id);
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate("/circuit/preview", {
      state: { circuit, metadata },
    });
  };

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
          "&:hover": {
            transform: onSelect ? "scale(1.03)" : undefined,
            boxShadow: onSelect ? "0 4px 20px rgba(0,0,0,0.12)" : undefined,
          },
        },
      })}
    >
      <Stack>
        {/* Header */}
        <Group justify="apart">
          <Group>
            <ThemeIcon size={30} radius="xl" color="blue" variant="light">
              <IconNetwork size={18} />
            </ThemeIcon>
            <Title order={4}>{metadata?.filename || "Unnamed Circuit"}</Title>
          </Group>
          <Badge variant="light" color="blue">
            {summary.n_qubits} Qubits
          </Badge>
        </Group>

        {/* Basic Stats */}
        <Group>
          <Text size="sm">Classical Bits: {summary.n_clbits}</Text>
          <Text size="sm">Depth: {summary.depth}</Text>
          <Text size="sm">Total Gates: {summary.n_gates}</Text>
        </Group>

        {/* Key Gate Badges */}
        <Group wrap="wrap">
          {summary.n_swap_gates > 0 && (
            <Badge color="red" variant="light">
              SWAP: {summary.n_swap_gates}
            </Badge>
          )}
          {summary.n_two_qubit_gates > 0 && (
            <Badge color="orange" variant="light">
              2Q: {summary.n_two_qubit_gates}
            </Badge>
          )}
        </Group>

        {/* Optional Preview / Actions */}
        <Group justify="right" mt="sm">
          <Button size="xs" variant="light" onClick={handlePreview}>
            Preview
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}
