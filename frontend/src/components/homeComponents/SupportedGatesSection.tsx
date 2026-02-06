import { Container, Title, Text, Card, Badge, SimpleGrid, Stack } from "@mantine/core";

interface GateCategory {
  name: string;
  gates: string;
}

const supportedGates: GateCategory[] = [
  { name: "Single-qubit", gates: "X, Y, Z, H, S, T, RX, RY, RZ" },
  { name: "Parametric", gates: "U3" },
  { name: "Two-qubit", gates: "CX, CZ" },
];

export function SupportedGatesSection() {
  return (
    <Container size="md" style={{ paddingBottom: 40 }}>
      <Title order={3} fw={600} size="h4" mb="md">
        Supported Gate Set
      </Title>
      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        {supportedGates.map((category) => (
          <Card key={category.name} withBorder radius="md" p="md">
            <Stack gap="xs">
              <Badge variant="light" size="lg">
                {category.name}
              </Badge>
              <Text size="sm" c="dimmed" fw={500}>
                {category.gates}
              </Text>
            </Stack>
          </Card>
        ))}
      </SimpleGrid>
      <Text size="sm" c="dimmed" style={{ marginTop: 12 }}>
        💡 <strong>Tip:</strong> Your circuit will be automatically normalized to our canonical basis. 
        Unsupported gates will be decomposed into supported ones.
      </Text>
    </Container>
  );
}