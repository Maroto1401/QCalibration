// Circuit info card - displays circuit filename, type, and file format details
import { Card, Group, ThemeIcon, Title, Text } from "@mantine/core";
import { IconBraces, IconFileCode, IconFileText } from "@tabler/icons-react";
import { CircuitMetadata } from "../../types"; 

export default function CircuitInfoCard({
  metadata,
}: {
  metadata: CircuitMetadata;
}) {
  const { filename, filetype } = metadata;

  const Icon = IconFileCode

  // Human-readable label
  const formatLabel =
    filetype === "qasm"
      ? "OpenQASM 2"
      : "OpenQASM 3";

  return (
    <Card padding="md" radius="md" withBorder>
      <Group align="center" gap="sm" wrap="nowrap">
        <ThemeIcon variant="light" size={42} radius="xl" color="blue">
          <Icon size={22} />
        </ThemeIcon>

        <div style={{ lineHeight: 1.2 }}>
          <Title order={5}>{filename}</Title>
          <Text size="sm" c="dimmed">
            {formatLabel}
          </Text>
        </div>
      </Group>
    </Card>
  );
}
