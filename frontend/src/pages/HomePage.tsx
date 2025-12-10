import { Container, Title, Text } from "@mantine/core";
import CircuitUploader from "../components/CircuitUploader";

export default function HomePage({ setCircuitId }: { setCircuitId: (c: any) => void }) {
  return (
    <Container size="md" style={{ paddingTop: 36 }}>
      <Title order={2}>QCal — Take Your Quantum Circuits Further</Title>
      <Text size="sm" style={{ marginTop: 8 }}>
        Upload a quantum circuit (OpenQASM2, OpenQASM3 or Qiskit-JSON).
      </Text>

      <div style={{ marginTop: 20 }}>
        <CircuitUploader circuitId={setCircuitId} />
      </div>
    </Container>
  );
}