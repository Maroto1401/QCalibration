import { Container, Title, Text, Loader, Alert, Grid} from "@mantine/core";
import { useEffect, useState } from "react";
import axios from "axios";

import MetricsCard from "../components/MetricsCard";
import GateBreakdownCard from "../components/GateBreakdownCard";
import CircuitIDCard from "../components/CircuitIDCard";

import { CircuitData } from "../types";
import TwoQubitGatesBreakdownDonut from "../components/TwoQubitGatesBreakdownDonut";



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
  console.log("Two Qubit Gates:", summary.two_qubit_gates);

return (
  <Container size="lg" style={{ paddingTop: 40 }}>
    <Title order={2} mb="lg">
      Circuit Analysis
    </Title>

    <Grid gutter="md">
      <Grid.Col span={{ base: 12, md: 8, lg: 8 }}>
        <MetricsCard summary={summary} />
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
        <GateBreakdownCard gateCounts={summary.gate_counts} />
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
        <TwoQubitGatesBreakdownDonut twoQubitGates={summary.two_qubit_gates}/>
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
        <CircuitIDCard id={circuit.circuit_id} />
      </Grid.Col>
    </Grid>
  </Container>
);

}
