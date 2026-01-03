import { Paper, Text, Title } from "@mantine/core";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";
import { CircuitSummary } from "../../types";

interface CircuitConnectivityHeatmapProps {
  circuit: CircuitSummary;
  height?: number;
}

export default function CircuitConnectivityHeatmap({
  circuit,
  height = 400,
}: CircuitConnectivityHeatmapProps) {
  const connectivity = circuit.circuitConnectivity || {};

  // Extract qubit indices
  const qubitsSet = new Set<number>();
  Object.keys(connectivity).forEach((key) => {
    const [q1, q2] = key.split("-").map(Number);
    qubitsSet.add(q1);
    qubitsSet.add(q2);
  });
  const qubits = Array.from(qubitsSet).sort((a, b) => a - b).map(String);

  // Prepare data for heatmap: [x, y, value]
  const data: [number, number, number][] = [];
  qubits.forEach((q1, i) => {
    qubits.forEach((q2, j) => {
      const key1 = `${q1}-${q2}`;
      const key2 = `${q2}-${q1}`; // symmetry
      const value = connectivity[key1] || connectivity[key2] || 0;
      data.push([i, j, value]);
    });
  });

  const option: echarts.EChartsOption = {
    tooltip: {
      formatter: (params: any) => {
        const val = params.value[2];
        return `Qubits ${qubits[params.value[0]]} ↔ ${qubits[params.value[1]]}: ${val}`;
      },
    },
    grid: {
      top: 60,
      left: 60,
      right: 20,
      bottom: 60, // leave space for tooltip / slider
    },
    xAxis: {
      type: "category",
      data: qubits,
      name: "Qubit",
      nameLocation: "middle",
      nameGap: 30,
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: "category",
      data: qubits,
      name: "Qubit",
      nameLocation: "middle",
      nameGap: 50,
    },
    visualMap: {
      min: 0,
      max: Math.max(...Object.values(connectivity), 1),
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 20,
      inRange: { color: ["#e0f3f8", "#0077b6"] },
    },
    series: [
      {
        name: "Connectivity",
        type: "heatmap",
        data: data,
        label: { show: true },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(0, 0, 0, 0.5)",
          },
        },
      },
    ],
  };

  if (!qubits.length) {
    return (
      <Paper p="md" withBorder>
        <Text>No connectivity data available</Text>
      </Paper>
    );
  }

  return (
    <Paper p="md" withBorder>
      <Title order={4} mb="sm">
        Circuit Connectivity Heatmap
      </Title>
      <ReactECharts
        option={option}
        style={{ height, width: "100%" }}
        opts={{ renderer: "svg" }}
      />
    </Paper>
  );
}


function buildHeatmapData(
  nQubits: number,
  connectivity: Record<string, number>
): number[][] {
  const data: number[][] = [];

  for (let i = 0; i < nQubits; i++) {
    for (let j = 0; j < nQubits; j++) {
      if (i === j) continue;

      const key =
        i < j ? `${i}-${j}` : `${j}-${i}`;
      const value = connectivity[key] ?? 0;

      data.push([j, i, value]);
    }
  }

  return data;
}
