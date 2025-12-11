import { Card } from "@mantine/core";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";

interface GateBreakdownCardProps {
  gateCounts: Record<string, number>;
}

export default function GateBreakdownCard({ gateCounts }: GateBreakdownCardProps) {
  // Convert to array and sort descending
  const sortedEntries = Object.entries(gateCounts).sort((a, b) => b[1] - a[1]);
  const dataAxis = sortedEntries.map(([gate]) => gate.toUpperCase());
  const data = sortedEntries.map(([, count]) => count);
  const yMax = Math.max(...data) * 1.1; // add 10% padding for shadow
  const dataShadow = data.map(() => yMax);

  const option = {
    title: {
      text: "Gate Breakdown of your Quantum Circuit",
      left: "center",
    },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#999" },
    },
    yAxis: {
      type: "category",
      data: dataAxis,
      axisLine: { show: false },
      axisTick: { show: false },
      inverse: true, // largest on top
      axisLabel: { color: "#000" },
    },
    grid: { left: 80, right: 40, top: 40, bottom: 40 },
    series: [
      {
        type: "bar",
        showBackground: true,
        backgroundStyle: { color: "rgba(180, 180, 180, 0.2)" },
        label: { show: true, position: "insideRight", color: "#fff" },
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#83bff6" },
            { offset: 0.5, color: "#188df0" },
            { offset: 1, color: "#188df0" },
          ]),
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: "#2378f7" },
              { offset: 0.7, color: "#2378f7" },
              { offset: 1, color: "#83bff6" },
            ]),
          },
        },
        data: data,
      },
    ],
  };

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <ReactECharts option={option} style={{ height: 400, width: "100%" }} />
    </Card>
  );
}
