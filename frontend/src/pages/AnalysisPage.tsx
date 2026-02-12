// Analysis page - visualizes circuit metrics, gates, connectivity, and operations
import { Container, Title, Text, Loader, Alert, Grid, Group, Divider, Stack} from "@mantine/core";
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from 'react-router-dom';

import MetricsCard from "../components/analysisComponents/MetricsCard";
import GateBreakdownCard from "../components/analysisComponents/GateBreakdownCard";
import CircuitInfoCard from "../components/analysisComponents/CircuitInfoCard";

import { CircuitData, CircuitMetadata } from "../types";
import TwoQubitGatesBreakdownDonut from "../components/analysisComponents/TwoQubitGatesBreakdownDonut";
import { IconCircuitResistor } from "@tabler/icons-react";
import { QuantumCircuitVisualizer } from "../components/analysisComponents/QuantumCircuitVisualizer";
import ToTopologyButton from "../components/analysisComponents/ToTopologyButton";
import CircuitConnectivityHeatmap from "../components/analysisComponents/circuitConnectivity";



export default function AnalysisPage({ circuitMetadata }: { circuitMetadata: CircuitMetadata}) {
  const circuitId = circuitMetadata.circuit_id;
  const [circuit, setCircuit] = useState<CircuitData | null>(null);
  const [loading, setLoading] = useState(!!circuitId);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const goToTopology = () => {
  if (!circuit) return;
  navigate("/topology", { state: { circuit } });
};

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

return (
  <Container size="lg" style={{ paddingTop: 40 }}>
    <Stack gap="sm">
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
    Quantum Circuit Analysis
  </Title>
</Group>
<Divider size="xs" label="A tool for researchers" labelPosition="center" />
    <Grid gutter="md">
      <Grid.Col span={{ base: 12, md: 4, lg: 4 }}>
        <CircuitInfoCard metadata={circuitMetadata} />
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 8, lg: 4 }}>
        <MetricsCard summary={summary} />
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 8, lg: 4 }}>
      <ToTopologyButton onClick={goToTopology} label="Add a Topology to your Circuit!" />
      </Grid.Col>
      
    </Grid>
    <Grid gutter="md">

      <Grid.Col span={{ base: 12, md: 6, lg: 8 }}>
        <GateBreakdownCard gateCounts={summary.gate_counts} />
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
        <TwoQubitGatesBreakdownDonut twoQubitGates={summary.two_qubit_gates}/>
      </Grid.Col>  
    </Grid>
    <Grid gutter="md">
  {/* <Grid.Col span={{ base: 12, md: 12, lg: 12 }}>
    <CircuitConnectivityHeatmap circuit={summary} height={400} />
</Grid.Col> */}
</Grid>
    <Grid gutter="md">
      <Grid.Col span={{ base: 12, md: 12, lg: 12}}>
        <QuantumCircuitVisualizer circuit={summary}  />
      </Grid.Col>
    </Grid>
    </Stack>
  </Container>
);

}
