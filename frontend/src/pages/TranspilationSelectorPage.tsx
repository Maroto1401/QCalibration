import { useState } from "react";
import axios from "axios";
import { TranspilationResult } from "../types";
import { Alert, Badge, Button, Container, Paper, Tabs, Title } from "@mantine/core";
import { TranspilationHeader } from "../components/TranspilationSelector/TranspilationHeader";
import { TranspilationTabContent } from "../components/TranspilationSelector/TranspilationTabContent";
import { useLocation, useNavigate } from "react-router-dom";
import { IconAlertCircle } from "@tabler/icons-react";
import { AlgorithmSelector } from "../components/TranspilationSelector/AlgorithmSelector";

type Status = 'pending' | 'running' | 'completed' | 'error';

interface ResultWithStatus {
  status: Status;
  data?: TranspilationResult;
  error?: string;
}

const TranspilationSelectorPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { topology, circuit } = location.state || {};

  const [results, setResults] = useState<Record<string, ResultWithStatus>>({
    default: { status: 'completed', data: circuit?.transpilationResult }
  });

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
    const newResults: Record<string, ResultWithStatus> = { ...results };
    algorithms.forEach(algo => {
      newResults[algo] = { status: 'pending' };
    });
    setResults(newResults);

    for (const algo of algorithms) {
      await handleTranspile(algo);
    }
  };

  const handleTranspile = async (algorithm: string) => {
    setResults(prev => ({
      ...prev,
      [algorithm]: { status: 'running' }
    }));

    try {
      const response = await axios.post<TranspilationResult>(
        "http://localhost:8000/transpile/run",
        {
          algorithm,
          circuit_id: circuit.circuit_id,
          topology: topology
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
  };

  const existingAlgorithms = Object.keys(results).filter(k => k !== 'default');

  return (
    <Container size="xl" py="md">
      <Title order={1} mb="lg">Quantum Circuit Transpilation</Title>

      <TranspilationHeader circuit={circuit} topology={topology} />

      <AlgorithmSelector
        onConfirm={handleAlgorithmConfirm}
        existingAlgorithms={existingAlgorithms}
      />

      <Paper p="md" withBorder>
        <Tabs defaultValue="default">
          <Tabs.List>
            <Tabs.Tab value="default">
              Default/Naive
              {results.default.status === 'completed' && <Badge size="xs" ml="xs" color="green">✓</Badge>}
              {results.default.status === 'running' && <Badge size="xs" ml="xs" color="blue">⏳</Badge>}
              {results.default.status === 'error' && <Badge size="xs" ml="xs" color="red">✗</Badge>}
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

          <Tabs.Panel value="default" pt="md">
            {results.default.data && (
              <TranspilationTabContent
                result={results.default.data}
                originalCircuit={circuit.summary}
                isDefault={true}
                onTranspile={() => {}}
              />
            )}
          </Tabs.Panel>

          {existingAlgorithms.map(algo => (
            results[algo].data ? (
              <Tabs.Panel key={algo} value={algo} pt="md">
                <TranspilationTabContent
                  result={results[algo].data!} // non-null assertion, safe due to conditional
                  originalCircuit={circuit.summary}
                  isDefault={false}
                  onTranspile={() => handleTranspile(algo)}
                />
              </Tabs.Panel>
            ) : null
          ))}
        </Tabs>
      </Paper>
    </Container>
  );
};

export default TranspilationSelectorPage;
