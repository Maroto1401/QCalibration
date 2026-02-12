// Circuit connectivity heatmap - visualizes qubit interaction frequencies
import { Paper, Text, Title, Slider, Group, Stack, Badge, Box } from '@mantine/core';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { useState, useMemo } from 'react';
import { CircuitSummary } from '../../types';

interface CircuitConnectivityHeatmapProps {
  circuit: CircuitSummary;
  height?: number;
}

export default function CircuitConnectivityHeatmap({
  circuit,
  height = 500,
}: CircuitConnectivityHeatmapProps) {
  const connectivity = circuit.circuitConnectivity || {};
  
  // Calculate min and max connectivity values
  const { minConnectivity, maxConnectivity, totalConnections } = useMemo(() => {
    const values = Object.values(connectivity);
    if (values.length === 0) return { minConnectivity: 0, maxConnectivity: 1, totalConnections: 0 };
    
    return {
      minConnectivity: Math.min(...values),
      maxConnectivity: Math.max(...values),
      totalConnections: values.reduce((sum, val) => sum + val, 0)
    };
  }, [connectivity]);
  
  // Slider state - initially show all gates
  const [minThreshold, setMinThreshold] = useState(minConnectivity);

  // Extract qubit indices
  const qubits = useMemo(() => {
    const qubitsSet = new Set<number>();
    Object.keys(connectivity).forEach((key) => {
      const [q1, q2] = key.split("-").map(Number);
      qubitsSet.add(q1);
      qubitsSet.add(q2);
    });
    return Array.from(qubitsSet).sort((a, b) => a - b);
  }, [connectivity]);

  // Prepare filtered data for heatmap
  const { filteredData, activeConnections, visiblePairs } = useMemo(() => {
    const data: [number, number, number][] = [];
    let activeCount = 0;
    let visibleCount = 0;
    
    qubits.forEach((q1, i) => {
      qubits.forEach((q2, j) => {
        if (i === j) {
          // Diagonal - no self-interaction
          data.push([i, j, -1]); // Use -1 to indicate diagonal
          return;
        }
        
        const qMin = Math.min(q1, q2);
        const qMax = Math.max(q1, q2);
        const key = `${qMin}-${qMax}`;
        const value = connectivity[key] || 0;
        if (value > 0) activeCount++;
        
        // Only show if value meets threshold
        if (value >= minThreshold && value > 0) {
          data.push([i, j, value]);
          visibleCount++;
        } else {
          data.push([i, j, 0]);
        }
      });
    });
    
    return { 
      filteredData: data, 
      activeConnections: activeCount / 2, // Divide by 2 since we count both directions
      visiblePairs: visibleCount / 2
    };
  }, [qubits, connectivity, minThreshold]);

  // ECharts option
  const option = useMemo(() => ({
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const val = params.value[2];
        if (val <= 0 || val === -1) return '';
        const q1 = qubits[params.value[0]];
        const q2 = qubits[params.value[1]];
        return `<strong>Q${q1} ↔ Q${q2}</strong><br/>${val} interaction${val > 1 ? 's' : ''}`;
      },
    },
    grid: {
      top: 50,
      left: 70,
      right: 100,
      bottom: 70,
    },
    xAxis: {
      type: 'category',
      data: qubits.map(q => `Q${q}`),
      name: 'Qubit',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 600,
      },
      axisLabel: { 
        rotate: 45,
        fontSize: 11,
        color: '#495057'
      },
      splitArea: {
        show: true,
      },
      axisLine: {
        lineStyle: {
          color: '#dee2e6'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: qubits.map(q => `Q${q}`),
      name: 'Qubit',
      nameLocation: 'middle',
      nameGap: 50,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 600,
      },
      axisLabel: {
        fontSize: 11,
        color: '#495057'
      },
      splitArea: {
        show: true,
      },
      axisLine: {
        lineStyle: {
          color: '#dee2e6'
        }
      }
    },
    visualMap: {
      type: 'continuous',
      show: true,
      min: 0,
      max: maxConnectivity,
      orient: 'vertical',
      right: 10,
      top: 'center',
      text: ['High', 'Low'],
      textStyle: {
        fontSize: 11,
        color: '#495057'
      },
      inRange: { 
        color: ['#f0f9ff', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7', '#0369a1']
      },
      formatter: (value: number) => value.toFixed(0)
    },
    series: [
      {
        name: 'Connectivity',
        type: 'heatmap',
        data: filteredData,
        label: { 
          show: true,
          fontSize: 11,
          fontWeight: 600,
          formatter: (params: any) => {
            const val = params.value[2];
            if (val === -1) return '—';
            return val > 0 ? val : '';
          },
          color: (params: any) => {
            const val = params.value[2];
            if (val === -1) return '#adb5bd';
            return val > maxConnectivity * 0.6 ? '#ffffff' : '#212529';
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
            borderWidth: 2,
            borderColor: '#1971c2'
          },
        },
        itemStyle: {
          borderWidth: 2,
          borderColor: '#ffffff',
          color: (params: any) => {
            const val = params.data[2];
            if (val === -1) return '#f1f3f5';
            return undefined;
          }
        }
      },
    ],
  }), [qubits, filteredData, maxConnectivity]);

  if (!qubits.length) {
    return (
      <Paper p="xl" withBorder radius="md">
        <Stack align="center" gap="xs">
          <Text size="lg" c="dimmed">No connectivity data available</Text>
          <Text size="sm" c="dimmed">Add gates to see qubit interactions</Text>
        </Stack>
      </Paper>
    );
  }

  return (
    <Paper p="lg" withBorder shadow="sm" radius="md">
      <Stack gap="lg">
        {/* Header */}
        <Group justify="space-between" align="flex-start">
          <Box>
            <Title order={3} mb={4}>Qubit Connectivity Map</Title>
            <Text size="sm" c="dimmed">
              Pairwise qubit interaction frequency
            </Text>
          </Box>
          <Group gap="xs">
            <Badge size="lg" color="blue" variant="light">
              {qubits.length} qubits
            </Badge>
            <Badge size="lg" color="cyan" variant="light">
              {totalConnections} total interactions
            </Badge>
          </Group>
        </Group>

        {/* Slider Control */}
        <Paper p="md" withBorder bg="gray.0" radius="md">
          <Stack gap="sm">
            <Group justify="space-between" align="center">
              <Text size="sm" fw={600} c="dark">
                Filter by minimum interactions
              </Text>
              <Group gap="xs">
                <Badge variant="dot" color="blue">
                  {visiblePairs} of {activeConnections} pairs shown
                </Badge>
                <Badge variant="filled" color="blue" size="lg">
                  ≥ {minThreshold}
                </Badge>
              </Group>
            </Group>
            <Slider
              value={minThreshold}
              onChange={setMinThreshold}
              min={minConnectivity}
              max={maxConnectivity}
              step={1}
              marks={[
                { value: minConnectivity, label: `${minConnectivity}` },
                { value: Math.floor((minConnectivity + maxConnectivity) / 2), label: `${Math.floor((minConnectivity + maxConnectivity) / 2)}` },
                { value: maxConnectivity, label: `${maxConnectivity}` },
              ]}
              color="blue"
              size="md"
            />
          </Stack>
        </Paper>

        {/* Heatmap */}
        <Box style={{ position: 'relative' }}>
          <ReactECharts
            option={option}
            style={{ height, width: '100%' }}
            opts={{ renderer: 'canvas' }}
          />
        </Box>

        {/* Legend */}
        <Paper p="sm" withBorder bg="gray.0" radius="md">
          <Text size="xs" c="dimmed" ta="center">
            The heatmap shows how many times each pair of qubits interacts through gates. 
            Hover over cells for details. The diagonal (—) represents self-interaction (always 0).
          </Text>
        </Paper>
      </Stack>
    </Paper>
  );
}