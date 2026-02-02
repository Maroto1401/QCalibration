import React, { useMemo } from "react";
import {
  Card,
  Grid,
  Title,
  Text,
  Tabs,
  Table,
  Group,
  Progress,
  Stack,
  Badge,
  SimpleGrid,
  ThemeIcon,
  Tooltip,
} from "@mantine/core";
import {
  IconAlertCircle,
  IconCheck,
  IconTrendingUp,
  IconClock,
  IconGauge,
  IconChartBar,
} from "@tabler/icons-react";
import ReactECharts from "echarts-for-react";
import { CircuitSummary, TranspilationResult } from "../../types";

export const TranspilationStatsTable: React.FC<{
  result: TranspilationResult;
  originalCircuit: CircuitSummary;
  normalizedCircuit: CircuitSummary;
  transpilledCircuit: CircuitSummary;
}> = ({ result, originalCircuit, normalizedCircuit, transpilledCircuit }) => {
  const metrics = result.metrics;

  // ---- Extract per_qubit_metrics for dependency tracking ----
  const perQubitMetrics = (metrics as any)?.per_qubit_metrics;

  // ---- Per-qubit data preparation (must be before early return) ----
  const perQubitData = useMemo(() => {
    if (!metrics) return [];
    if (!perQubitMetrics || Object.keys(perQubitMetrics).length === 0) return [];
    const data = Object.entries(perQubitMetrics).map(([phys_q, details]: [string, any]) => ({
      qubit: `Q${phys_q}`,
      execution_time_ns: (details.execution_time as number) * 1e9, // in nanoseconds for chart
      execution_time_us: (details.execution_time as number) * 1e6, // in microseconds for display
      t1_error: (details.t1_error as number) * 100,
      t2_error: (details.t2_error as number) * 100,
      decoherence: (details.decoherence_error as number) * 100,
    }));
    return data;
  }, [metrics, perQubitMetrics]);

  if (!result.metrics || !transpilledCircuit) return null;

  // ---- helpers ----
  const pct = (delta: number, base: number) =>
    base === 0 ? "—" : `${((delta / base) * 100).toFixed(1)}%`;

  const deltaLabel = (value: number, base: number) => {
    const d = value - base;
    if (d === 0) return null;
    return `${d > 0 ? "+" : ""}${d} (${pct(d, base)})`;
  };

  const nSwapTranspiled = metrics.n_swap_gates ?? 0;

  // ---- comparison rows ----
  const comparisonData = [
    {
      metric: "Total Gates",
      original: originalCircuit.n_gates,
      normalized: normalizedCircuit.n_gates,
      transpiled: transpilledCircuit.n_gates,
    },
    {
      metric: "Two-Qubit Gates",
      original: originalCircuit.n_two_qubit_gates,
      normalized: normalizedCircuit.n_two_qubit_gates,
      transpiled: transpilledCircuit.n_two_qubit_gates,
    },
    {
      metric: "Circuit Depth",
      original: originalCircuit.depth,
      normalized: normalizedCircuit.depth,
      transpiled: transpilledCircuit.depth,
    },
    {
      metric: "SWAP Gates",
      original: originalCircuit.n_swap_gates ?? 0,
      normalized: normalizedCircuit.n_swap_gates ?? 0,
      transpiled: nSwapTranspiled,
    },
  ];

  // ---- File download and clipboard helpers ----
  const downloadTextFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
  };


  // ---- Helper to get status icon ----
  const getErrorStatus = (error: number) => {
    if (error < 0.01) return { color: "green", icon: IconCheck };
    if (error < 0.05) return { color: "yellow", icon: IconTrendingUp };
    return { color: "red", icon: IconAlertCircle };
  };

  return (
    <Stack gap="lg">
      <Card withBorder p="lg" radius="md">
        <Stack gap="md">
          <Title order={3}>Circuit Transpilation & Metrics Analysis</Title>

          <Tabs defaultValue="overview" variant="pills">
            <Tabs.List>
              <Tabs.Tab value="overview" leftSection={<IconGauge size={14} />}>
                Overview
              </Tabs.Tab>
              <Tabs.Tab value="error-breakdown" leftSection={<IconAlertCircle size={14} />}>
                Error Breakdown
              </Tabs.Tab>
              <Tabs.Tab value="fidelity" leftSection={<IconChartBar size={14} />}>
                Fidelity Analysis
              </Tabs.Tab>
              <Tabs.Tab value="per-qubit" leftSection={<IconClock size={14} />}>
                Per-Qubit Metrics
              </Tabs.Tab>
              <Tabs.Tab value="qasm" leftSection={<IconGauge size={14} />}>
                QASM
              </Tabs.Tab>

            </Tabs.List>

            {/* ---- TAB 1: OVERVIEW ---- */}
            <Tabs.Panel value="overview" pt="xl">
              <Stack gap="lg">
                <div style={{ overflowX: "auto" }}>
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th align="center" style={{ textAlign: "center" }}>Metric</Table.Th>
                        <Table.Th align="center" style={{ textAlign: "center" }}>Original</Table.Th>
                        <Table.Th align="center" style={{ textAlign: "center" }}>Normalized</Table.Th>
                        <Table.Th align="center" style={{ textAlign: "center" }}>Transpiled</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {comparisonData.map((row, idx) => (
                        <Table.Tr key={idx}>
                          <Table.Td align="center" fw={500}>{row.metric}</Table.Td>
                          <Table.Td align="center">{row.original}</Table.Td>
                          <Table.Td align="center">
                            <Stack gap={2}>
                              <span>{row.normalized}</span>
                              {row.normalized !== row.original && (
                                <Text size="xs" c="dimmed">
                                  {deltaLabel(row.normalized, row.original)}
                                </Text>
                              )}
                            </Stack>
                          </Table.Td>
                          <Table.Td align="center">
                            <Stack gap={2}>
                              <span>{row.transpiled}</span>
                              {row.transpiled !== row.normalized && (
                                <Text
                                  size="xs"
                                  fw={600}
                                  c={row.transpiled > row.normalized ? "red" : "green"}
                                >
                                  {deltaLabel(row.transpiled, row.normalized)}
                                </Text>
                              )}
                            </Stack>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </div>

                <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
                  <Card withBorder p="md" radius="md" bg="violet.0">
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                        Execution Time
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="violet">
                        <IconClock size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="violet">
                      {(metrics.overall_execution_time * 1e6).toFixed(2)} μs
                    </Text>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="blue.0">
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                        Original Depth
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="blue">
                        <IconChartBar size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="blue">
                      {metrics.original_depth}
                    </Text>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="cyan.0">
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                        Transpiled Depth
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="cyan">
                        <IconTrendingUp size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="cyan">
                      {metrics.transpiled_depth}
                    </Text>
                    <Text size="xs" c="dimmed" mt={4}>
                      Δ {metrics.depth_increase > 0 ? "+" : ""}
                      {metrics.depth_increase}
                    </Text>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="grape.0">
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                        Total Gates
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="grape">
                        <IconGauge size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="grape">
                      {metrics.total_gates}
                    </Text>
                  </Card>
                </SimpleGrid>

                <Card withBorder p="md" radius="md">
                  <Text size="sm" fw={600} mb="md">
                    Depth Comparison
                  </Text>
                  <ReactECharts
                    option={{
                      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
                      xAxis: {
                        type: "category",
                        data: ["Original", "Transpiled"],
                        axisLabel: { color: "#666" },
                      },
                      yAxis: {
                        type: "value",
                        axisLabel: { color: "#666" },
                      },
                      series: [
                        {
                          data: [metrics.original_depth, metrics.transpiled_depth],
                          type: "bar",
                          itemStyle: { color: "#4C6EF5", borderRadius: [8, 8, 0, 0] },
                        },
                      ],
                      grid: { top: 20, right: 30, bottom: 30, left: 60 },
                    }}
                    style={{ height: "300px" }}
                  />
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* ---- TAB 2: ERROR BREAKDOWN ---- */}
            <Tabs.Panel value="error-breakdown" pt="xl">
              <Stack gap="lg">
                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                  <Card withBorder p="md" radius="md">
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                          Gate Error
                        </Text>
                        <Badge color="red" variant="light">
                          {(metrics.overall_gate_error * 100).toFixed(3)}%
                        </Badge>
                      </Group>
                      <Progress
                        value={metrics.overall_gate_error * 100}
                        color="red"
                        size="md"
                        radius="md"
                      />
                      <Text size="xs" c="dimmed">
                        Fidelity: {(metrics.gate_fidelity * 100).toFixed(2)}%
                      </Text>
                    </Stack>
                  </Card>

                  <Card withBorder p="md" radius="md">
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                          Readout Error
                        </Text>
                        <Badge color="orange" variant="light">
                          {(metrics.overall_readout_error * 100).toFixed(3)}%
                        </Badge>
                      </Group>
                      <Progress
                        value={metrics.overall_readout_error * 100}
                        color="orange"
                        size="md"
                        radius="md"
                      />
                      <Text size="xs" c="dimmed">
                        Avg: {(metrics.avg_readout_error * 100).toFixed(3)}% | Fidelity:{" "}
                        {(metrics.readout_fidelity * 100).toFixed(2)}%
                      </Text>
                    </Stack>
                  </Card>

                  <Card withBorder p="md" radius="md">
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                          Decoherence Error
                        </Text>
                        <Badge color="yellow" variant="light">
                          {(metrics.avg_decoherence_error * 100).toFixed(3)}%
                        </Badge>
                      </Group>
                      <Progress
                        value={metrics.avg_decoherence_error * 100}
                        color="yellow"
                        size="md"
                        radius="md"
                      />
                      <Text size="xs" c="dimmed">
                        Fidelity: {(metrics.decoherence_fidelity * 100).toFixed(2)}%
                      </Text>
                    </Stack>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="pink.0">
                    <Stack gap="sm">
                      <Group justify="space-between">
                        <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                          Effective Error
                        </Text>
                        <Badge color="pink" variant="light">
                          {(metrics.effective_error * 100).toFixed(2)}%
                        </Badge>
                      </Group>
                      <Progress
                        value={metrics.effective_error * 100}
                        color="pink"
                        size="md"
                        radius="md"
                      />
                      <Text size="xs" c="dimmed">
                        Combined from all sources
                      </Text>
                    </Stack>
                  </Card>
                </SimpleGrid>

                <Card withBorder p="md" radius="md">
                  <Text size="sm" fw={600} mb="md">
                    Error Sources Distribution
                  </Text>
                  <ReactECharts
                    option={{
                      tooltip: {
                        trigger: "axis",
                        axisPointer: { type: "shadow" },
                        formatter: (params: any) => {
                          if (Array.isArray(params)) {
                            return `${params[0].name}<br/>${params[0].value.toFixed(3)}%`;
                          }
                          return params.value.toFixed(3) + "%";
                        },
                      },
                      xAxis: {
                        type: "category",
                        data: ["Gate Error", "Readout Error", "Decoherence Error"],
                        axisLabel: { color: "#666", interval: 0, rotate: 15 },
                      },
                      yAxis: {
                        type: "value",
                        axisLabel: { color: "#666", formatter: "{value}%" },
                      },
                      series: [
                        {
                          data: [
                            metrics.overall_gate_error * 100,
                            metrics.overall_readout_error * 100,
                            metrics.avg_decoherence_error * 100,
                          ],
                          type: "bar",
                          itemStyle: { color: "#FA5252", borderRadius: [8, 8, 0, 0] },
                        },
                      ],
                      grid: { top: 20, right: 30, bottom: 60, left: 60 },
                    }}
                    style={{ height: "300px" }}
                  />
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* ---- TAB 3: FIDELITY ANALYSIS ---- */}
            <Tabs.Panel value="fidelity" pt="xl">
              <Stack gap="lg">
                <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
                  <Card withBorder p="md" radius="md" bg="green.0">
                    <Group justify="space-between" mb="sm">
                      <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                        Gate Fidelity
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="green">
                        <IconCheck size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="green">
                      {(metrics.gate_fidelity * 100).toFixed(4)}%
                    </Text>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="teal.0">
                    <Group justify="space-between" mb="sm">
                      <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                        Readout Fidelity
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="teal">
                        <IconCheck size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="teal">
                      {(metrics.readout_fidelity * 100).toFixed(4)}%
                    </Text>
                  </Card>

                  <Card withBorder p="md" radius="md" bg="blue.0">
                    <Group justify="space-between" mb="sm">
                      <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                        Decoherence Fidelity
                      </Text>
                      <ThemeIcon size="lg" radius="md" variant="light" color="blue">
                        <IconCheck size={18} />
                      </ThemeIcon>
                    </Group>
                    <Text size="xl" fw={700} c="blue">
                      {(metrics.decoherence_fidelity * 100).toFixed(4)}%
                    </Text>
                  </Card>
                </SimpleGrid>

                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                  <Card withBorder p="md" radius="md" bg="grape.0">
                    <Stack gap="md">
                      <div>
                        <Text size="sm" fw={600} c="dimmed" tt="uppercase" mb="sm">
                          Total Circuit Fidelity
                        </Text>
                        <Text size="2xl" fw={700} c="grape">
                          {(metrics.fidelity * 100).toFixed(2)}%
                        </Text>
                      </div>
                      <Text size="xs" c="dimmed">
                        <strong>Formula:</strong> Gate × Readout × Decoherence
                      </Text>
                      <Text size="xs" c="dimmed" style={{ fontFamily: "monospace" }}>
                        {(metrics.gate_fidelity * 100).toFixed(4)}% × {(metrics.readout_fidelity * 100).toFixed(4)}% ×{" "}
                        {(metrics.decoherence_fidelity * 100).toFixed(4)}%
                      </Text>
                    </Stack>
                  </Card>

                  <Card withBorder p="md" radius="md">
                    <Text size="sm" fw={600} mb="md">
                      Fidelity Components
                    </Text>
                    <ReactECharts
                      option={{
                        tooltip: { trigger: "item", formatter: "{b}: {c}%" },
                        series: [
                          {
                            name: "Fidelity",
                            type: "pie",
                            radius: "50%",
                            data: [
                              {
                                value: metrics.gate_fidelity * 100,
                                name: "Gate",
                                itemStyle: { color: "#4C6EF5" },
                              },
                              {
                                value: metrics.readout_fidelity * 100,
                                name: "Readout",
                                itemStyle: { color: "#15AABF" },
                              },
                              {
                                value: metrics.decoherence_fidelity * 100,
                                name: "Decoherence",
                                itemStyle: { color: "#FCC419" },
                              },
                            ],
                            emphasis: {
                              itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: "rgba(0, 0, 0, 0.5)",
                              },
                            },
                            label: {
                              formatter: "{b}: {c:.2f}%",
                            },
                          },
                        ],
                      }}
                      style={{ height: "300px" }}
                    />
                  </Card>
                </SimpleGrid>
              </Stack>
            </Tabs.Panel>

            {/* ---- TAB 4: PER-QUBIT METRICS ---- */}
            <Tabs.Panel value="per-qubit" pt="xl">
              <Stack gap="lg">
                {(metrics as any).per_qubit_metrics && Object.keys((metrics as any).per_qubit_metrics).length > 0 ? (
                  <>
                    <Card withBorder p="md" radius="md">
                      <Text size="sm" fw={600} mb="md">
                        Per-Qubit Execution & Decoherence
                      </Text>
                      <div style={{ overflowX: "auto" }}>
                        <Table striped highlightOnHover>
                          <Table.Thead>
                            <Table.Tr>
                              <Table.Th align="center" style={{ textAlign: "center" }}>Qubit</Table.Th>
                              <Table.Th align="center" style={{ textAlign: "center" }}>Exec. Time (μs)</Table.Th>
                              <Table.Th align="center" style={{ textAlign: "center" }}>T1 Error (%)</Table.Th>
                              <Table.Th align="center" style={{ textAlign: "center" }}>T2 Error (%)</Table.Th>
                              <Table.Th align="center" style={{ textAlign: "center" }}>Total Decoherence (%)</Table.Th>
                            </Table.Tr>
                          </Table.Thead>
                          <Table.Tbody>
                            {Object.entries((metrics as any).per_qubit_metrics).map(([phys_q, details]: [string, any]) => {
                              const decohError = details.decoherence_error as number;
                              const status = getErrorStatus(decohError);
                              const StatusIcon = status.icon;
                              const execTimeUs = (details.execution_time as number) * 1e6; // Convert to microseconds
                              return (
                                <Table.Tr key={phys_q}>
                                  <Table.Td align="center" fw={500}>
                                    <Badge size="sm" variant="dot">
                                      Q{phys_q}
                                    </Badge>
                                  </Table.Td>
                                  <Table.Td align="center">
                                    <Text size="sm">{execTimeUs.toFixed(3)} </Text>
                                  </Table.Td>
                                  <Table.Td align="center">
                                    <Badge
                                      color={
                                        (details.t1_error as number) > 0.01 ? "red" : "green"
                                      }
                                      variant="light"
                                    >
                                      {((details.t1_error as number) * 100).toFixed(3)}%
                                    </Badge>
                                  </Table.Td>
                                  <Table.Td align="center">
                                    <Badge
                                      color={
                                        (details.t2_error as number) > 0.01 ? "orange" : "green"
                                      }
                                      variant="light"
                                    >
                                      {((details.t2_error as number) * 100).toFixed(3)}%
                                    </Badge>
                                  </Table.Td>
                                  <Table.Td align="center">
                                    <Group gap={4} justify="center">
                                      <Badge
                                        color={
                                          decohError > 0.02
                                            ? "red"
                                            : decohError > 0.01
                                              ? "yellow"
                                              : "green"
                                        }
                                        variant="light"
                                      >
                                        {(decohError * 100).toFixed(3)}%
                                      </Badge>
                                      <StatusIcon size={16} color={status.color} />
                                    </Group>
                                  </Table.Td>
                                </Table.Tr>
                              );
                            })}
                          </Table.Tbody>
                        </Table>
                      </div>
                    </Card>

                    {perQubitData.length > 0 && (
                      <Card withBorder p="md" radius="md">
                        <Text size="sm" fw={600} mb="md">
                          Execution Time Distribution (μs)
                        </Text>
                        <ReactECharts
                          option={{
                            tooltip: {
                              trigger: "axis",
                              axisPointer: { type: "shadow" },
                              formatter: (params: any) => {
                                if (Array.isArray(params)) {
                                  const value = params[0].value;
                                  return `${params[0].name}<br/>${value.toFixed(3)} ns`;
                                }
                                return params.value.toFixed(3) + " ns";
                              },
                            },
                            xAxis: {
                              type: "category",
                              data: perQubitData.map((d) => d.qubit),
                              axisLabel: { color: "#666" },
                            },
                            yAxis: {
                              type: "value",
                              axisLabel: { color: "#666", formatter: (val: number) => val.toFixed(0) },
                              name: "Execution Time (μs)",
                            },
                            series: [
                              {
                                data: perQubitData.map((d) => d.execution_time_us),
                                type: "bar",
                                itemStyle: { color: "#4C6EF5", borderRadius: [8, 8, 0, 0] },
                              },
                            ],
                            grid: { top: 20, right: 30, bottom: 30, left: 60 },
                          }}
                          style={{ height: "300px" }}
                        />
                      </Card>
                    )}

                    {perQubitData.length > 0 && (
                      <Card withBorder p="md" radius="md">
                        <Text size="sm" fw={600} mb="md">
                          Decoherence Errors by Qubit
                        </Text>
                        <ReactECharts
                          option={{
                            tooltip: { trigger: "axis", formatter: (params: any) => {
                              if (!Array.isArray(params)) return params.value.toFixed(3) + "%";
                              let result = params[0].axisValue + "<br/>";
                              params.forEach((param: any) => {
                                result += `${param.marker} ${param.seriesName}: ${param.value.toFixed(3)}%<br/>`;
                              });
                              return result;
                            } },
                            legend: { 
                              data: ["T1 Error", "T2 Error", "Total Decoherence"], 
                              textStyle: { color: "#666" },
                              bottom: 0,
                              left: "center"
                            },
                            xAxis: {
                              type: "category",
                              data: perQubitData.map((d) => d.qubit),
                              axisLabel: { color: "#666" },
                            },
                            yAxis: {
                              type: "value",
                              axisLabel: { color: "#666", formatter: "{value}%" },
                            },
                            series: [
                              {
                                name: "T1 Error",
                                type: "line",
                                data: perQubitData.map((d) => d.t1_error),
                                stroke: "#FA5252",
                                itemStyle: { color: "#FA5252" },
                                symbolSize: 6,
                              },
                              {
                                name: "T2 Error",
                                type: "line",
                                data: perQubitData.map((d) => d.t2_error),
                                stroke: "#FCC419",
                                itemStyle: { color: "#FCC419" },
                                symbolSize: 6,
                              },
                              {
                                name: "Total Decoherence",
                                type: "line",
                                data: perQubitData.map((d) => d.decoherence),
                                stroke: "#4C6EF5",
                                itemStyle: { color: "#4C6EF5" },
                                symbolSize: 6,
                                lineStyle: { width: 2 },
                              },
                            ],
                            grid: { top: 30, right: 30, bottom: 60, left: 60 },
                          }}
                          style={{ height: "400px" }}
                        />
                      </Card>
                    )}

                    <Card withBorder p="md" radius="md" bg="gray.0">
                      <Stack gap="sm">
                        <Text size="sm" fw={600} tt="uppercase" c="dimmed">
                          Metric Definitions
                        </Text>
                        <Stack gap={8}>
                          <div>
                            <Text size="xs" fw={600}>
                              Execution Time (μs)
                            </Text>
                            <Text size="xs" c="dimmed">
                              Total time this qubit is active (involved in gate operations)
                            </Text>
                          </div>
                          <div>
                            <Text size="xs" fw={600}>
                              T1 Error (%)
                            </Text>
                            <Text size="xs" c="dimmed">
                              Probability of energy relaxation during execution: 1 - exp(-t_exec / T1)
                            </Text>
                          </div>
                          <div>
                            <Text size="xs" fw={600}>
                              T2 Error (%)
                            </Text>
                            <Text size="xs" c="dimmed">
                              Probability of dephasing during execution: 1 - exp(-t_exec / T2)
                            </Text>
                          </div>
                          <div>
                            <Text size="xs" fw={600}>
                              Total Decoherence Error (%)
                            </Text>
                            <Text size="xs" c="dimmed">
                              Combined T1 + T2 decoherence error using rate: 1 - exp(-t_exec × (1/T1 + 1/T2))
                            </Text>
                          </div>
                        </Stack>
                      </Stack>
                    </Card>
                  </>
                ) : (
                  <Card withBorder p="md" radius="md">
                    <Text c="dimmed" ta="center">
                      No per-qubit metrics available
                    </Text>
                  </Card>
                )}
              </Stack>
            </Tabs.Panel>

            {/* ---- TAB 5: QASM EXPORT ---- */}

            <Tabs.Panel value="qasm" pt="xl">
              <Stack gap="lg">
                <Card withBorder p="md" radius="md">
                  <Title order={4}>Circuit QASM2 Export</Title>
                  <Text size="sm" c="dimmed">
                    Download or copy the OpenQASM 2.0 representations of the circuits.
                  </Text>
                </Card>

                {/* ---- Normalized (Basis) Circuit ---- */}
                <Card withBorder p="md" radius="md">
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text fw={600}>Normalized (Basis) Circuit</Text>
                      <Group gap="xs">
                        <Tooltip label="Copy QASM to clipboard">
                          <Badge
                            variant="light"
                            color="blue"
                            style={{ cursor: "pointer" }}
                            onClick={() => copyToClipboard(result.normalized_qasm2)}
                          >
                            Copy
                          </Badge>
                        </Tooltip>
                        <Tooltip label="Download QASM file">
                          <Badge
                            variant="light"
                            color="green"
                            style={{ cursor: "pointer" }}
                            onClick={() =>
                              downloadTextFile(
                                result.normalized_qasm2,
                                `normalized_${result.algorithm}.qasm`
                              )
                            }
                          >
                            Download
                          </Badge>
                        </Tooltip>
                      </Group>
                    </Group>

                    <pre
                      style={{
                        maxHeight: 300,
                        overflow: "auto",
                        background: "#f8f9fa",
                        padding: "12px",
                        borderRadius: "6px",
                        fontSize: "12px",
                      }}
                    >
                      {result.normalized_qasm2}
                    </pre>
                  </Stack>
                </Card>

                {/* ---- Fully Transpiled Circuit ---- */}
                <Card withBorder p="md" radius="md">
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Text fw={600}>Fully Transpiled (Routed) Circuit</Text>
                      <Group gap="xs">
                        <Tooltip label="Copy QASM to clipboard">
                          <Badge
                            variant="light"
                            color="blue"
                            style={{ cursor: "pointer" }}
                            onClick={() => copyToClipboard(result.transpiled_qasm2)}
                          >
                            Copy
                          </Badge>
                        </Tooltip>
                        <Tooltip label="Download QASM file">
                          <Badge
                            variant="light"
                            color="green"
                            style={{ cursor: "pointer" }}
                            onClick={() =>
                              downloadTextFile(
                                result.transpiled_qasm2,
                                `transpiled_${result.algorithm}.qasm`
                              )
                            }
                          >
                            Download
                          </Badge>
                        </Tooltip>
                      </Group>
                    </Group>

                    {/* ---- Embedding Info ---- */}
                    {result.embedding && (
                      <Card withBorder radius="sm" p="sm" bg="gray.0">
                        <Stack gap={4}>
                          <Text size="sm" fw={500}>
                            Final Qubit Embedding (Logical → Physical)
                          </Text>

                          {/* Show as pretty JSON for readability */}
                          <pre
                            style={{
                              fontSize: "12px",
                              margin: 0,
                              whiteSpace: "pre-wrap",
                            }}
                          >
                            {JSON.stringify(result.embedding, null, 2)}
                          </pre>

                          <Group justify="flex-end">
                            <Badge
                              variant="light"
                              color="gray"
                              style={{ cursor: "pointer" }}
                              onClick={() =>
                                copyToClipboard(JSON.stringify(result.embedding, null, 2))
                              }
                            >
                              Copy embedding JSON
                            </Badge>
                          </Group>
                        </Stack>
                      </Card>
                    )}


                    {/* ---- QASM ---- */}
                    <pre
                      style={{
                        maxHeight: 300,
                        overflow: "auto",
                        background: "#f8f9fa",
                        padding: "12px",
                        borderRadius: "6px",
                        fontSize: "12px",
                      }}
                    >
                      {result.transpiled_qasm2}
                    </pre>
                  </Stack>
                </Card>

              </Stack>
            </Tabs.Panel>

          </Tabs>
        </Stack>
      </Card>
    </Stack>
  );
};