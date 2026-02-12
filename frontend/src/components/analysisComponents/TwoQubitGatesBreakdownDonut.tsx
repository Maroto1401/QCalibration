// Two-qubit gates breakdown - donut chart showing 2Q gate distribution
import { Card, Text, Badge, Group } from "@mantine/core";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";

interface TwoQubitDonutProps {
  twoQubitGates: Record<string, number>; // e.g., { cx: 12, swap: 5 }
  maxDisplayGates?: number; // Maximum number of gate types to display
}

// Define colors for common two-qubit gates
const GATE_COLORS: Record<string, string> = {
  cx: "#3B82F6",      // Blue
  cnot: "#3B82F6",    // Blue (same as cx)
  cz: "#8B5CF6",      // Purple
  swap: "#10B981",    // Green
  cy: "#F59E0B",      // Amber
  iswap: "#06B6D4",   // Cyan
  cswap: "#14B8A6",   // Teal
  dcx: "#6366F1",     // Indigo
  ecr: "#EC4899",     // Pink
  rxx: "#EF4444",     // Red
  ryy: "#F97316",     // Orange
  rzz: "#84CC16",     // Lime
};

// Fallback colors for unknown gates
const FALLBACK_COLORS = [
  "#64748B", "#94A3B8", "#CBD5E1", 
  "#475569", "#334155", "#1E293B"
];

export default function TwoQubitGatesBreakdownDonut({ 
  twoQubitGates, 
  maxDisplayGates = 10 
}: TwoQubitDonutProps) {
  // Sort gates by count (descending)
  const sortedEntries = Object.entries(twoQubitGates)
    .sort(([, a], [, b]) => b - a);

  // If there are more gates than maxDisplayGates, group the rest into "Others"
  let dataEntries;
  let hasOthers = false;
  
  if (sortedEntries.length > maxDisplayGates) {
    const topGates = sortedEntries.slice(0, maxDisplayGates - 1);
    const otherGates = sortedEntries.slice(maxDisplayGates - 1);
    const otherCount = otherGates.reduce((sum, [, count]) => sum + count, 0);
    
    dataEntries = [
      ...topGates.map(([gate, count]) => ({
        name: gate.toUpperCase(),
        value: count,
        itemStyle: { color: GATE_COLORS[gate.toLowerCase()] || FALLBACK_COLORS[0] }
      })),
      {
        name: "OTHERS",
        value: otherCount,
        itemStyle: { color: "#9CA3AF" }
      }
    ];
    hasOthers = true;
  } else {
    dataEntries = sortedEntries.map(([gate, count], idx) => ({
      name: gate.toUpperCase(),
      value: count,
      itemStyle: { 
        color: GATE_COLORS[gate.toLowerCase()] || FALLBACK_COLORS[idx % FALLBACK_COLORS.length] 
      }
    }));
  }

  const totalGates = sortedEntries.reduce((sum, [, count]) => sum + count, 0);

  const option: echarts.EChartsOption = {
    title: {
      text: "Two-Qubit Gates",
      left: "center",
      textStyle: {
        fontSize: 16,
        fontWeight: "bold"
      }
    },
    tooltip: { 
      trigger: "item", 
      formatter: "{b}: {c} ({d}%)" 
    },
    legend: {
      orient: "horizontal",
      bottom: 10,
      left: "center",
      type: "scroll",
    },
    series: [
      {
        name: "Two-Qubit Gates",
        type: "pie",
        radius: ["40%", "70%"], // Donut
        label: { 
          show: true, 
          formatter: "{b}: {c}",
          fontSize: 11
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0,0,0,0.5)",
          },
        },
        data: dataEntries,
      },
    ],
  };

  if (totalGates === 0) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Text ta="center" c="dimmed">No two-qubit gates in circuit</Text>
      </Card>
    );
  }

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" mb="xs">
        <Badge color="blue" variant="light">
          {sortedEntries.length} gate types
        </Badge>
        <Badge color="gray" variant="filled">
          {totalGates} total
        </Badge>
      </Group>
      
      {hasOthers && (
        <Text size="xs" c="dimmed" mb="sm">
          Showing top {maxDisplayGates - 1} gate types. Others grouped.
        </Text>
      )}
      
      <ReactECharts 
        option={option} 
        style={{ height: 350, width: "100%" }} 
        opts={{ renderer: "svg" }}
      />
    </Card>
  );
}