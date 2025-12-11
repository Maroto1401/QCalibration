import { Card, Title, Text } from "@mantine/core";

export default function CircuitIDCard({ id }: { id: string }) {
  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Title order={4} mb="sm">Circuit ID</Title>

      <Text size="sm" style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
        {id}
      </Text>
    </Card>
  );
}
