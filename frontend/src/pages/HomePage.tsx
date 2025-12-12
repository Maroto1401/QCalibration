import { Container, Title, Text, Group } from "@mantine/core";
import CircuitUploader from "../components/CircuitUploader";
import { CircuitMetadata } from "../types";
import { IconCircuitResistor } from "@tabler/icons-react";

export default function HomePage({
  setCircuitMetadata,
}: {
  setCircuitMetadata: (m: CircuitMetadata) => void;
}) {
  return (
    <Container size="md" style={{ paddingTop: 36 }}>
      <Group justify="center" align="center" gap="xs">
      <IconCircuitResistor size={32} stroke={1.5} color="#228BE6" />
      <Title 
        order={2}
        fw={700}
        style={{
          background: "linear-gradient(45deg, #228BE6 0%, #15AABF 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}
      >
        QCal - Take your Quantum Circuits to the Next Level
      </Title>
      <Text> Upload a quantum circuit (OpenQASM2, OpenQASM3) to start optimizing</Text>
    </Group>

      <div style={{ marginTop: 20 }}>
        <CircuitUploader setCircuitMetadata={setCircuitMetadata} />
      </div>
    </Container>
  );
}

