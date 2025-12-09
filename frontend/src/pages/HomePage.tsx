import { Container, Title, Text } from "@mantine/core";
import { useNavigate } from "react-router-dom";
import CircuitUploader from "../components/CircuitUploader";

export default function HomePage({ setCircuit }: { setCircuit: (c: any) => void }) {
  const navigate = useNavigate();

  const handleParsed = (parsed: any) => {
    setCircuit(parsed);
    navigate("/circuit-analysis"); // navigate after backend returns parsed circuit
  };

  return (
    <Container size="md" style={{ paddingTop: 36 }}>
      <Title order={2}>QCal — Take Your Quantum Circuits Further</Title>
      <Text size="sm" style={{ marginTop: 8 }}>
        Upload a quantum circuit (OpenQASM2, OpenQASM3 or JSON).
      </Text>

      <div style={{ marginTop: 20 }}>
        <CircuitUploader onFile={handleParsed} />
      </div>
    </Container>
  );
}