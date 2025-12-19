import { Card, Text, Stack, Group } from "@mantine/core";
import { TranspilationResult } from "../../types";
import ReactECharts from "echarts-for-react";

export const TranspilationStatsChart: React.FC<{
  result: TranspilationResult;
  originalCircuit: any;
}> = ({ result, originalCircuit }) => {
  if (!result.metrics || !result.summary) return null;

  // Approximate SWAP gates if not explicitly provided
  const nSwapTranspiled = result.summary.n_swap_gates ?? Math.round(
    (result.summary.n_cx_gates - originalCircuit.n_cx_gates) / 3
  );

  const chartOption = {
    title: {
      text: "Circuit Metrics Comparison",
      left: "center",
      top: 10,
      textStyle: { fontSize: 18, fontWeight: 600 },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
    },
    legend: {
      data: ["Original Circuit", "Transpiled Circuit"],
      top: 45,
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: 90,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: ["Total Gates", "2Q Gates", "Depth", "CX Gates", "SWAP Gates"],
      axisLabel: { interval: 0, rotate: 0 },
    },
    yAxis: {
      type: "value",
      name: "Count",
    },
    series: [
      {
        name: "Original Circuit",
        type: "bar",
        data: [
          originalCircuit.n_gates,
          originalCircuit.n_two_qubit_gates,
          originalCircuit.depth,
          originalCircuit.n_cx_gates,
          originalCircuit.n_swap_gates,
        ],
        itemStyle: { color: "#228be6" },
        label: { show: true, position: "top" },
      },
      {
        name: "Transpiled Circuit",
        type: "bar",
        data: [
          result.summary.n_gates,
          result.summary.n_two_qubit_gates,
          result.summary.depth,
          result.summary.n_cx_gates,
          nSwapTranspiled,
        ],
        itemStyle: { color: "#fa5252" },
        label: { show: true, position: "top" },
      },
    ],
  };

  const performanceOption = {
    title: {
      text: "Performance Metrics",
      left: "center",
      top: 10,
      textStyle: { fontSize: 18, fontWeight: 600 },
    },
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c}%",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: 60,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: ["Gate Error", "Decoherence Risk", "Readout Error", "Effective Error", "Fidelity"],
    },
    yAxis: {
      type: "value",
      name: "Percentage (%)",
      max: 100,
    },
    series: [
      {
        name: "Performance",
        type: "bar",
        data: [
          { value: (result.metrics.gate_error * 100).toFixed(2), itemStyle: { color: "#fa5252" } },
          { value: (result.metrics.decoherence_risk * 100).toFixed(2), itemStyle: { color: "#f59f00" } },
          { value: (result.metrics.readout_error * 100).toFixed(2), itemStyle: { color: "#228be6" } },
          { value: (result.metrics.effective_error * 100).toFixed(2), itemStyle: { color: "#7950f2" } },
          { value: (result.metrics.fidelity * 100).toFixed(2), itemStyle: { color: "#51cf66" } },
        ],
        label: {
          show: true,
          position: "top",
          formatter: "{c}%",
        },
      },
    ],
  };

  return (
    <Stack gap="lg">
      <Card withBorder p="lg">
        <ReactECharts option={chartOption} style={{ height: "400px" }} />
      </Card>

      <Card withBorder p="lg">
        <ReactECharts option={performanceOption} style={{ height: "300px" }} />
      </Card>

      <Card withBorder p="md">
        <Group justify="space-around">
          <Stack gap={4} align="center">
            <Text size="xs" c="dimmed" tt="uppercase">Gates Inserted</Text>
            <Text size="xl" fw={700}>{result.metrics.gates_inserted}</Text>
          </Stack>
          <Stack gap={4} align="center">
            <Text size="xs" c="dimmed" tt="uppercase">Depth Increase</Text>
            <Text size="xl" fw={700}>+{result.metrics.depth_increase}</Text>
          </Stack>
          <Stack gap={4} align="center">
            <Text size="xs" c="dimmed" tt="uppercase">Execution Time</Text>
            <Text size="xl" fw={700}>{result.metrics.execution_time.toFixed(2)} ms</Text>
          </Stack>
        </Group>
      </Card>
    </Stack>
  );
};
