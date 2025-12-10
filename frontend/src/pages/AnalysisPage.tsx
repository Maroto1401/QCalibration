import { Container, Title, Text, Loader, Alert, Badge } from "@mantine/core";
import { useEffect, useState } from "react";
import axios from "axios";

type CircuitData = {
  circuit_id: string;
  summary: {
    n_qubits: number;
    n_clbits: number;
    n_gates: number;
    gate_names: string[];
  };
};

export default function AnalysisPage({ circuitId }: { circuitId?: string }) {
  const [circuit, setCircuit] = useState<CircuitData | null>(null);
  const [loading, setLoading] = useState(!!circuitId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!circuitId) {
      setError("No circuit ID provided");
      setLoading(false);
      return;
    }

    const fetchCircuit = async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/circuit/${circuitId}`
        );
        setCircuit(response.data);
        setError(null);
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Failed to fetch circuit");
      } finally {
        setLoading(false);
      }
    };

    fetchCircuit();
  }, [circuitId]);

  if (!circuitId) {
    return (
      <Container>
        <Alert color="yellow" title="No Circuit">
          No circuit ID provided. Upload a circuit first.
        </Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container style={{ textAlign: "center", paddingTop: 40 }}>
        <Loader />
        <Text style={{ marginTop: 10 }}>Loading circuit...</Text>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert color="red" title="Error">
          {error}
        </Alert>
      </Container>
    );
  }

  if (!circuit) {
    return (
      <Container>
        <Alert color="orange" title="No Data">
          No circuit data available.
        </Alert>
      </Container>
    );
  }

  const { summary } = circuit;
  const gateCount: Record<string, number> = {};
  summary.gate_names.forEach((gate) => {
    gateCount[gate] = (gateCount[gate] || 0) + 1;
  });

  return (
    <Container size="md" style={{ paddingTop: 20 }}>
      <Title order={2}>Circuit Analysis</Title>

      <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ border: "1px solid #e0e0e0", padding: 12, borderRadius: 4 }}>
          <Title order={4}>Circuit Metrics</Title>
          <div style={{ display: "flex", gap: 24, marginTop: 12 }}>
            <div>
              <Text size="sm" color="dimmed">
                Qubits
              </Text>
              <Text style={{ fontWeight: 500, fontSize: 18 }}>
                {summary.n_qubits}
              </Text>
            </div>
            <div>
              <Text size="sm" color="dimmed">
                Classical Bits
              </Text>
              <Text style={{ fontWeight: 500, fontSize: 18 }}>
                {summary.n_clbits}
              </Text>
            </div>
            <div>
              <Text size="sm" color="dimmed">
                Total Gates
              </Text>
              <Text style={{ fontWeight: 500, fontSize: 18 }}>
                {summary.n_gates}
              </Text>
            </div>
          </div>
        </div>

        <div style={{ border: "1px solid #e0e0e0", padding: 12, borderRadius: 4 }}>
          <Title order={4}>Gate Breakdown</Title>
          <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
            {Object.entries(gateCount).map(([gate, count]) => (
              <Badge key={gate} size="lg">
                {gate}: {count}
              </Badge>
            ))}
          </div>
        </div>

        <div style={{ border: "1px solid #e0e0e0", padding: 12, borderRadius: 4 }}>
          <Title order={4}>Circuit ID</Title>
          <Text
            size="sm"
            style={{
              marginTop: 8,
              fontFamily: "monospace",
              wordBreak: "break-all",
            }}
          >
            {circuit.circuit_id}
          </Text>
        </div>
      </div>
    </Container>
  );
}
