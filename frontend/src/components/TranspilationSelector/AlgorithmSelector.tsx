import { Alert, Button, Card, Checkbox, Grid, Group, Paper, Stack, Title, Text, Badge } from "@mantine/core";
import { IconAlertCircle, IconRefresh } from "@tabler/icons-react";
import { useState } from "react";

export const AlgorithmSelector: React.FC<{
  onConfirm: (algorithms: string[]) => void;
  existingAlgorithms: string[];
}> = ({ onConfirm, existingAlgorithms }) => {
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<string[]>([]);
  
  const algorithms = [
    { 
      id: 'naive', 
      name: 'Naive Swap', 
      description: 'Simple greedy approach for quick transpilation',
      recommended: true 
    },
    { 
      id: 'sabre', 
      name: 'SABRE', 
      description: 'Heuristic bidirectional search algorithm for optimal qubit routing',
      recommended: true 
    },
    { 
      id: 'lookahead', 
      name: 'Lookahead Swap', 
      description: 'Forward-looking optimization with depth awareness',
      recommended: false 
    },
    { 
      id: 'basic', 
      name: 'Basic Swap', 
      description: 'Simple greedy approach for quick transpilation',
      recommended: false 
    },
  ];
  
  const toggleAlgorithm = (id: string) => {
    if (existingAlgorithms.includes(id)) return;
    setSelectedAlgorithms(prev => 
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    );
  };
  
  const availableAlgorithms = algorithms.filter(a => !existingAlgorithms.includes(a.id));
  
  return (
    <Paper p="xl" withBorder mb="md">
      <Stack gap="lg">
        <div>
          <Title order={3} mb="xs">Select Transpilation Algorithms</Title>
          <Text size="sm" c="dimmed">
            Choose one or more routing algorithms to compare. The Default/Naive transpilation is always included as a baseline.
          </Text>
        </div>
        
        {availableAlgorithms.length === 0 ? (
          <Alert icon={<IconAlertCircle size={16} />} color="blue" variant="light">
            All available algorithms have been executed. Results are shown in the tabs below.
          </Alert>
        ) : (
          <>
            <Grid>
              {algorithms.map(algo => {
                const isAlreadyRun = existingAlgorithms.includes(algo.id);
                return (
                  <Grid.Col span={6} key={algo.id}>
                    <Card 
                      padding="md" 
                      withBorder
                      style={{ 
                        cursor: isAlreadyRun ? 'not-allowed' : 'pointer',
                        opacity: isAlreadyRun ? 0.5 : 1,
                        border: selectedAlgorithms.includes(algo.id) ? '2px solid #228be6' : undefined
                      }}
                      onClick={() => !isAlreadyRun && toggleAlgorithm(algo.id)}
                    >
                      <Group justify="space-between" align="flex-start">
                        <Stack gap="xs" style={{ flex: 1 }}>
                          <Group gap="xs">
                            <Text fw={600} size="lg">{algo.name}</Text>
                            {algo.recommended && !isAlreadyRun && (
                              <Badge size="xs" color="green" variant="light">Recommended</Badge>
                            )}
                            {isAlreadyRun && (
                              <Badge size="xs" color="gray" variant="light">Already Run</Badge>
                            )}
                          </Group>
                          <Text size="sm" c="dimmed">{algo.description}</Text>
                        </Stack>
                        <Checkbox
                          checked={selectedAlgorithms.includes(algo.id)}
                          disabled={isAlreadyRun}
                          onChange={() => {}}
                          size="md"
                        />
                      </Group>
                    </Card>
                  </Grid.Col>
                );
              })}
            </Grid>
            
            <Alert icon={<IconAlertCircle size={16} />} color="blue" variant="light">
              Selected algorithms will be executed sequentially. You can always run additional transpilations later.
            </Alert>
            
            <Button 
              size="lg"
              fullWidth 
              onClick={() => onConfirm(selectedAlgorithms)}
              disabled={selectedAlgorithms.length === 0}
              leftSection={<IconRefresh size={20} />}
            >
              Run Selected Transpilations ({selectedAlgorithms.length} algorithm{selectedAlgorithms.length !== 1 ? 's' : ''})
            </Button>
          </>
        )}
      </Stack>
    </Paper>
  );
};