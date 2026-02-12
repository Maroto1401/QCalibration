// Transpilation selector page - run and compare transpilation algorithms
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { TranspilationResult, CircuitSummary } from "../types";
import { Alert, Badge, Button, Container, Paper, Tabs, Title, Group, Loader, Text } from "@mantine/core";
import { TranspilationHeader } from "../components/TranspilationSelector/TranspilationHeader";
import { TranspilationTabContent } from "../components/TranspilationSelector/TranspilationTabContent";
import { useLocation, useNavigate } from "react-router-dom";
import { IconAlertCircle, IconMap } from "@tabler/icons-react";
import { QuantumCircuitVisualizer } from "../components/analysisComponents/QuantumCircuitVisualizer";
import { AlgorithmSelector } from "../components/TranspilationSelector/AlgorithmSelector";
import { EmbeddingVisualization } from "../components/TranspilationSelector/EmbeddingVisualization";
import { ErrorEstimatesSection } from "../components/TranspilationSelector/ErrorEstimatesSection";


type Status = 'pending' | 'running' | 'completed' | 'error';

interface ResultWithStatus {
  status: Status;
  data?: TranspilationResult;
  error?: string;
}

interface NormalizedCircuitResponse {
  circuit_id: string;
  normalized_summary: CircuitSummary;
}

const TranspilationSelectorPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { topology, circuit } = location.state || {};

  const [results, setResults] = useState<Record<string, ResultWithStatus>>({
    naive: { status: 'pending', data: circuit?.transpilationResult }
  });

  const [normalizedCircuit, setNormalizedCircuit] = useState<{
  status: 'loading' | 'loaded' | 'error';
  circuitId?: string;        // ✅ store normalized circuit ID
  data?: CircuitSummary;     // keep summary for visualization
  error?: string;
}>({ status: 'loading' });


  const [embeddingView, setEmbeddingView] = useState<{
    opened: boolean;
    embedding: TranspilationResult['embedding'] | null;
    algorithmName: string;
  }>({ opened: false, embedding: null, algorithmName: '' });

  // Fetch normalized circuit
useEffect(() => {
  const fetchNormalizedCircuit = async () => {
    if (!circuit?.circuit_id || !topology?.basisGates) return;

    try {
      // Build query string manually
      const params = topology.basisGates.map((g: string) => `target_basis=${encodeURIComponent(g)}`).join('&');
      const url = `http://localhost:8000/normalize/circuit/${circuit.circuit_id}?${params}`;

      console.log("Fetching normalized circuit with URL:", url); // debug

      const response = await axios.get<NormalizedCircuitResponse>(url);

setNormalizedCircuit({
  status: 'loaded',
  circuitId: response.data.circuit_id,  // ✅ save normalized circuit ID
  data: response.data.normalized_summary
});

    } catch (err: any) {
      setNormalizedCircuit({
        status: 'error',
        error: err?.response?.data?.detail || "Failed to normalize circuit"
      });
    }
  };

  fetchNormalizedCircuit();
}, [circuit?.circuit_id, topology?.basisGates]);


  const handleTranspile = useCallback(
  async (algorithm: string) => {
    if (!normalizedCircuit.circuitId) return;

    setResults(prev => ({
      ...prev,
      [algorithm]: { status: 'running' }
    }));

    try {
      const response = await axios.post<TranspilationResult>(
        "http://localhost:8000/transpile/run",
        {
          algorithm,
          circuit_id: normalizedCircuit.circuitId,  // ✅ send the normalized circuit ID
          topology
        }
      );

      setResults(prev => ({
        ...prev,
        [algorithm]: { status: 'completed', data: response.data }
      }));
    } catch (err: any) {
      setResults(prev => ({
        ...prev,
        [algorithm]: {
          status: 'error',
          error: err?.response?.data?.detail || "Transpilation failed"
        }
      }));
    }
  },
  [normalizedCircuit.circuitId, topology]
);



  useEffect(() => {
  if (
    results.naive.status === 'pending' &&
    normalizedCircuit.status === 'loaded' &&
    normalizedCircuit.circuitId
  ) {
    handleTranspile('naive');
  }
}, [results.naive.status, normalizedCircuit, handleTranspile]);



  if (!topology || !circuit) {
    return (
      <Container size="xl" py="md">
        <Alert icon={<IconAlertCircle size={16} />} color="red" title="Missing Data">
          No circuit or topology data provided. Please select a circuit and topology first.
        </Alert>
        <Button mt="md" onClick={() => navigate(-1)}>Go Back</Button>
      </Container>
    );
  }

  const handleAlgorithmConfirm = async (algorithms: string[]) => {
  if (normalizedCircuit.status !== 'loaded' || !normalizedCircuit.circuitId) return;

  const newResults: Record<string, ResultWithStatus> = { ...results };
  algorithms.forEach(algo => {
    newResults[algo] = { status: 'pending' };
  });
  setResults(newResults);

  for (const algo of algorithms) {
    await handleTranspile(algo);
  }
};


  const handleViewEmbedding = (algorithm: string) => {
    const result = results[algorithm];
    if (result.data?.embedding) {
      setEmbeddingView({
        opened: true,
        embedding: result.data.embedding,
        algorithmName: algorithm,
      });
    }
  };

  const existingAlgorithms = Object.keys(results).filter(k => k !== 'naive');

  return (
    <><Container size="xl" py="md">
      <Title order={1} mb="lg">Quantum Circuit Transpilation</Title>

      <TranspilationHeader circuit={circuit} topology={topology} />

      {/* Normalized Circuit Visualizer */}
      <Paper p="md" withBorder mb="lg">
        <Title order={3} mb="md">Normalized Circuit</Title>
        {normalizedCircuit.status === 'loading' && (
          <Group justify="center" p="xl">
            <Loader size="md" />
            <Text>Loading normalized circuit...</Text>
          </Group>
        )}
        {normalizedCircuit.status === 'error' && (
          <Alert icon={<IconAlertCircle size={16} />} color="red" title="Normalization Error">
            {normalizedCircuit.error}
          </Alert>
        )}
        {normalizedCircuit.status === 'loaded' && normalizedCircuit.data && (
          <QuantumCircuitVisualizer circuit={normalizedCircuit.data} />
        )}
      </Paper>

      <AlgorithmSelector
        onConfirm={handleAlgorithmConfirm}
        existingAlgorithms={existingAlgorithms} />

      <Paper p="md" withBorder>
        <Tabs defaultValue="naive">
          <Tabs.List>
            <Tabs.Tab value="naive">
              Naive
              {results.naive.status === 'completed' && <Badge size="xs" ml="xs" color="green">✓</Badge>}
              {results.naive.status === 'running' && <Badge size="xs" ml="xs" color="blue">⏳</Badge>}
              {results.naive.status === 'error' && <Badge size="xs" ml="xs" color="red">✗</Badge>}
            </Tabs.Tab>
            {existingAlgorithms.map(algo => (
              <Tabs.Tab key={algo} value={algo}>
                {algo.toUpperCase()}
                {results[algo].status === 'completed' && <Badge size="xs" ml="xs" color="green">✓</Badge>}
                {results[algo].status === 'running' && <Badge size="xs" ml="xs" color="blue">⏳</Badge>}
                {results[algo].status === 'error' && <Badge size="xs" ml="xs" color="red">✗</Badge>}
              </Tabs.Tab>
            ))}
          </Tabs.List>

          <Tabs.Panel value="naive" pt="md">
            {results.naive.data && (
              <>
                <TranspilationTabContent
                  result={results.naive.data}
                  originalCircuit={circuit.summary}
                  normalizedCircuit={normalizedCircuit.data}
                  isDefault={true}
                  onTranspile={() => { } } />
                {results.naive.data.embedding && (
                  <Group mt="md">
                    <Button
                      leftSection={<IconMap size={18} />}
                      variant="light"
                      onClick={() => handleViewEmbedding('naive')}
                    >
                      View Embedding on Topology
                    </Button>
                  </Group>
                )}
              </>
            )}
          </Tabs.Panel>

          {existingAlgorithms.map(algo => (
            results[algo].data ? (
              <Tabs.Panel key={algo} value={algo} pt="md">
                <TranspilationTabContent
                  result={results[algo].data!}
                  originalCircuit={circuit.summary}
                  normalizedCircuit={normalizedCircuit.data}
                  isDefault={false}
                  onTranspile={() => handleTranspile(algo)} />
                {results[algo].data!.embedding && (
                  <Group mt="md">
                    <Button
                      leftSection={<IconMap size={18} />}
                      variant="light"
                      onClick={() => handleViewEmbedding(algo)}
                    >
                      View Embedding on Topology
                    </Button>
                  </Group>
                )}
              </Tabs.Panel>
            ) : null
          ))}
        </Tabs>
      </Paper>

      <EmbeddingVisualization
        topology={topology}
        embedding={embeddingView.embedding}
        opened={embeddingView.opened}
        onClose={() => setEmbeddingView({ opened: false, embedding: null, algorithmName: '' })}
        algorithmName={embeddingView.algorithmName} />

    </Container>
    <ErrorEstimatesSection /></>

  );
};

export default TranspilationSelectorPage;