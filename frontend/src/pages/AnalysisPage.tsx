import { Container, Title, Text } from "@mantine/core";

export default function AnalysisPage({ circuit }: { circuit: any }) {
  return (
    <Container>
      <Title order={3}>Circuit Analysis</Title>
      <pre style={{ marginTop: 20 }}>
        {JSON.stringify(circuit, null, 2)}
      </pre>
    </Container>
  );
}
