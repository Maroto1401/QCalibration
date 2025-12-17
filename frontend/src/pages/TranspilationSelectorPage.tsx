import { useState } from "react";
import { TranspilationResult } from "../types";
import { Alert, Badge, Button, Container, Paper, Tabs, Title } from "@mantine/core";
import { TranspilationHeader } from "../components/TranspilationSelector/TranspilationHeader";
import {TranspilationTabContent} from "../components/TranspilationSelector/TranspilationTabContent";
import { useLocation, useNavigate } from "react-router-dom";
import { IconAlertCircle } from "@tabler/icons-react";
import { AlgorithmSelector } from "../components/TranspilationSelector/AlgorithmSelector";


const TranspilationSelectorPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { topology, circuit } = location.state || {};
  
  const [results, setResults] = useState<Record<string, TranspilationResult>>({
    default: {
      algorithm: 'Default/Naive',
      status: 'completed',
      metrics: {
        error_rate: 0.0234,
        gates_inserted: 12,
        depth_increase: 8,
        execution_time: 45.3,
        fidelity: 0.9766
      },
      circuit: circuit?.summary
    }
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
    const newResults = { ...results };
    
    algorithms.forEach(algo => {
      newResults[algo] = {
        algorithm: algo.toUpperCase(),
        status: 'pending'
      };
    });
    
    setResults(newResults);
    
    // Auto-run all selected algorithms
    for (const algo of algorithms) {
      await handleTranspile(algo);
    }
  };
  
  const handleTranspile = async (algorithm: string) => {
    setResults(prev => ({
      ...prev,
      [algorithm]: { ...prev[algorithm], status: 'running' }
    }));
    
    // TODO: Replace with actual API call
    // const response = await fetch('/api/transpile', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ 
    //     algorithm, 
    //     circuit_id: circuit.circuit_id, 
    //     topology_id: topology.id 
    //   })
    // });
    // const data = await response.json();
    
    setTimeout(() => {
      setResults(prev => ({
        ...prev,
        [algorithm]: {
          ...prev[algorithm],
          status: 'completed',
          metrics: {
            error_rate: Math.random() * 0.05,
            gates_inserted: Math.floor(Math.random() * 20) + 5,
            depth_increase: Math.floor(Math.random() * 15) + 3,
            execution_time: Math.random() * 100 + 20,
            fidelity: 0.95 + Math.random() * 0.04
          },
          circuit: {
            ...circuit.summary,
            n_gates: circuit.summary.n_gates + Math.floor(Math.random() * 20) + 5,
            n_two_qubit_gates: circuit.summary.n_two_qubit_gates + Math.floor(Math.random() * 10),
            depth: circuit.summary.depth + Math.floor(Math.random() * 15) + 3,
            n_swap_gates: Math.floor(Math.random() * 8) + 2
          }
        }
      }));
    }, 2000);
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
              <Badge size="xs" ml="xs" color="green">✓</Badge>
            </Tabs.Tab>
            {Object.keys(results).filter(k => k !== 'default').map(algo => (
              <Tabs.Tab key={algo} value={algo}>
                {algo.toUpperCase()}
                {results[algo].status === 'completed' && (
                  <Badge size="xs" ml="xs" color="green">✓</Badge>
                )}
                {results[algo].status === 'running' && (
                  <Badge size="xs" ml="xs" color="blue">⏳</Badge>
                )}
              </Tabs.Tab>
            ))}
          </Tabs.List>
          
          <Tabs.Panel value="default" pt="md">
            <TranspilationTabContent
              result={results.default}
              originalCircuit={circuit.summary}
              isDefault={true}
              onTranspile={() => {}}
            />
          </Tabs.Panel>
          
          {Object.keys(results).filter(k => k !== 'default').map(algo => (
            <Tabs.Panel key={algo} value={algo} pt="md">
              <TranspilationTabContent
                result={results[algo]}
                originalCircuit={circuit.summary}
                isDefault={false}
                onTranspile={() => handleTranspile(algo)}
              />
            </Tabs.Panel>
          ))}
        </Tabs>
      </Paper>
    </Container>
  );
};

export default TranspilationSelectorPage;