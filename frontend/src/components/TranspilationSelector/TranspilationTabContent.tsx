import { Button, Card, Group, Stack, Text } from "@mantine/core";
import { IconChartLine, IconRefresh, IconTable } from "@tabler/icons-react";
import { TranspilationResult } from "../../types";
import { useState } from "react";
import { TranspilationStatsTable } from "./TranspilationStatsTable";
import { TranspilationStatsChart } from "./TranspilationStatsChart";

export const TranspilationTabContent: React.FC<{
  result: TranspilationResult;
  originalCircuit: any;
  normalizedCircuit: any;
  isDefault: boolean;
  onTranspile: () => void;
}> = ({ result, originalCircuit, normalizedCircuit, isDefault, onTranspile }) => {
  const [viewMode, setViewMode] = useState<'table' | 'chart'>('table');

  // Pending state for non-default algorithms
  if (!isDefault && (!result.metrics || !result.summary)) {
    return (
      <Card withBorder>
        <Stack align="center" gap="md" py="xl">
          <IconRefresh size={48} stroke={1.5} color="#868e96" />
          <Text size="lg" c="dimmed">Transpilation not yet executed</Text>
          <Button 
            size="lg"
            leftSection={<IconRefresh size={16} />}
            onClick={onTranspile}
          >
            Run {result.algorithm} Transpilation
          </Button>
        </Stack>
      </Card>
    );
  }

  // Running state
  if (!result.metrics || !result.summary) {
    return (
      <Card withBorder>
        <Stack align="center" gap="md" py="xl">
          <Text size="lg">Running transpilation...</Text>
        </Stack>
      </Card>
    );
  }

  // Completed state
  return (
    <Stack gap="md">
      <Group justify="flex-end">
        <Button 
          variant="light" 
          leftSection={viewMode === 'table' ? <IconChartLine size={16} /> : <IconTable size={16} />}
          onClick={() => setViewMode(prev => prev === 'table' ? 'chart' : 'table')}
        >
          Switch to {viewMode === 'table' ? 'Chart' : 'Table'} View
        </Button>
      </Group>

      {viewMode === 'table' ? (
        <TranspilationStatsTable 
          result={result} 
          originalCircuit={originalCircuit} 
          normalizedCircuit={normalizedCircuit}
          transpilledCircuit={result.summary}
        />
      ) : (
        <TranspilationStatsChart 
          result={result} 
          originalCircuit={originalCircuit}
          normalizedCircuit={normalizedCircuit}
          transpilledCircuit={result.summary}
        />
      )}
    </Stack>
  );
};