import { Paper, Text, Title, Slider, Group, Stack, Badge } from '@mantine/core';
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
  height = 400,
}: CircuitConnectivityHeatmapProps) {
  const connectivity = circuit.circuitConnectivity || {};
  
  // Calculate min and max connectivity values
  const connectivityValues = Object.values(connectivity);
  const minConnectivity = Math.min(...connectivityValues, 0);
  const maxConnectivity = Math.max(...connectivityValues, 1);
  
  // Slider state - initially show all gates
  const [minThreshold, setMinThreshold] = useState(minConnectivity);

  // Extract qubit indices
  const qubitsSet = new Set<number>();
  Object.keys(connectivity).forEach((key) => {
    const [q1, q2] = key.split("-").map(Number);
    qubitsSet.add(q1);
    qubitsSet.add(q2);
  });
  const qubits = Array.from(qubitsSet).sort((a, b) => a - b).map(String);

  // Prepare filtered data for heatmap
  const { filteredData, activeConnections } = useMemo(() => {
    const data: [number, number, number][] = [];
    let activeCount = 0;
    
    qubits.forEach((q1, i) => {
      qubits.forEach((q2, j) => {
        const key1 = `${q1}-${q2}`;
        const key2 = `${q2}-${q1}`;
        const value = connectivity[key1] || connectivity[key2] || 0;
        
        // Only include if value meets threshold
        if (value >= minThreshold) {
          data.push([i, j, value]);
          if (value > 0) activeCount++;
        } else {
          // Push null for cells below threshold to hide them
          data.push([i, j, 0]);
        }
      });
    });
    
    return { filteredData: data, activeConnections: activeCount };
  }, [qubits, connectivity, minThreshold]);

  // ECharts option
  const option: echarts.EChartsOption = useMemo(() => ({
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const val = params.value[2];
        if (val === 0) return '';
        return `Qubits ${qubits[params.value[0]]} ↔ ${qubits[params.value[1]]}: ${val}`;
      },
    },
    grid: {
      top: 40,
      left: 80,
      right: 20,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: qubits,
      name: 'Qubit',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: { 
        rotate: 45,
        fontSize: 11
      },
      splitArea: {
        show: true,
      },
    },
    yAxis: {
      type: 'category',
      data: qubits,
      name: 'Qubit',
      nameLocation: 'middle',
      nameGap: 50,
      axisLabel: {
        fontSize: 11
      },
      splitArea: {
        show: true,
      },
    },
    visualMap: {
      show: false,
      min: 0,
      max: maxConnectivity,
      inRange: { 
        color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'] 
      },
    },
    series: [
      {
        name: 'Connectivity',
        type: 'heatmap',
        data: filteredData,
        label: { 
          show: true,
          fontSize: 10,
          formatter: (params: any) => {
            return params.value[2] > 0 ? params.value[2] : '';
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        itemStyle: {
          borderWidth: 1,
          borderColor: '#fff'
        }
      },
    ],
  }), [qubits, filteredData, maxConnectivity]);

  if (!qubits.length) {
    return (
      <Paper p="md" withBorder>
        <Text>No connectivity data available</Text>
      </Paper>
    );
  }

  return (
    <Paper p="md" withBorder shadow="sm">
      <Stack gap="md">
        <Group justify="space-between" align="center">
          <Title order={4}>Circuit Connectivity Heatmap</Title>
          <Badge color="blue" variant="light">
            {activeConnections} active connections
          </Badge>
        </Group>

        {/* Slider Control */}
        <Paper p="md" withBorder bg="gray.0">
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" fw={500}>
                Minimum Gate Connectivity
              </Text>
              <Badge variant="filled" color="blue">
                {minThreshold}
              </Badge>
            </Group>
            <Slider
              value={minThreshold}
              onChange={setMinThreshold}
              min={minConnectivity}
              max={maxConnectivity}
              step={1}
              marks={[
                { value: minConnectivity, label: String(minConnectivity) },
                { value: maxConnectivity, label: String(maxConnectivity) },
              ]}
              color="blue"
              size="md"
            />
          </Stack>
        </Paper>

        {/* Heatmap */}
        <ReactECharts
          option={option}
          style={{ height, width: '100%' }}
          opts={{ renderer: 'svg' }}
        />
      </Stack>
    </Paper>
  );
}