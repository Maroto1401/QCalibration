import { Card } from "@mantine/core";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";

interface TwoQubitDonutProps {
  twoQubitGates: Record<string, number>; // e.g., { cx: 12, swap: 5 }
}

export default function TwoQubitGatesBreakdownDonut({ twoQubitGates }: TwoQubitDonutProps) {
  // Prepare data for the chart
  const dataEntries = Object.entries(twoQubitGates).map(([gate, count]) => ({
    name: gate.toUpperCase(),
    value: count,
  }));

  const option = {
    title: {
      text: "Two-Qubit Gates",
      left: "center",
    },
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    legend: {
    orient: "horizontal",
    bottom: 10,
    left: "center",
    },
    series: [
      {
        name: "Two-Qubit Gates",
        type: "pie",
        radius: ["40%", "70%"], // Donut
        label: { show: true, formatter: "{b}: {c}" },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0,0,0,0.5)",
          },
        },
        itemStyle: {
          color: (params: any) =>
            new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: "#83bff6" },
              { offset: 0.5, color: "#188df0" },
              { offset: 1, color: "#2378f7" },
            ]),
        },
        data: dataEntries,
      },
    ],
  };

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder >
      <ReactECharts option={option} style={{ height: 350, width: "100%" }} />
    </Card>
  );
}
