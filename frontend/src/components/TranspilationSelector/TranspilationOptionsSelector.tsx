import { Card, Grid, Group, Paper, Switch, Title, Text, Button} from "@mantine/core";
import { useState } from "react";

export const TranspilationOptionsSelector: React.FC<{
  onSelect: (algorithms: string[]) => void;
}> = ({ onSelect }) => {
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<string[]>(['sabre', 'stochastic']);
  
  const algorithms = [
    { id: 'naive', name: 'Naive', description: 'Simple greedy approach' },
    { id: 'sabre', name: 'SABRE', description: 'Heuristic bidirectional search' },
    { id: 'lookahead', name: 'Lookahead', description: 'Forward-looking optimization' },
    { id: 'basic', name: 'Basic', description: 'Simple greedy approach' },
  ];
  
  const toggleAlgorithm = (id: string) => {
    setSelectedAlgorithms(prev => 
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    );
  };
  
  return (
    <Paper p="md" mb="md" withBorder>
      <Title order={4} mb="md">Select Transpilation Algorithms</Title>
      <Grid>
        {algorithms.map(algo => (
          <Grid.Col span={6} key={algo.id}>
            <Card padding="sm" withBorder>
              <Group justify="space-between">
                <div>
                  <Text fw={500}>{algo.name}</Text>
                  <Text size="xs" c="dimmed">{algo.description}</Text>
                </div>
                <Switch
                  checked={selectedAlgorithms.includes(algo.id)}
                  onChange={() => toggleAlgorithm(algo.id)}
                />
              </Group>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
      <Button 
        mt="md" 
        fullWidth 
        onClick={() => onSelect(selectedAlgorithms)}
        disabled={selectedAlgorithms.length === 0}
      >
        Configure Transpilation Options
      </Button>
    </Paper>
  );
};
