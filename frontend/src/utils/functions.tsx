import { Topology } from "../types";
import * as echarts from "echarts";

export function getConnectivityMeta(connectivity: Topology["connectivity"]) {
  switch (connectivity) {
    case "very high":
      return { color: "blue", label: "VERY HIGH" };
    case "high":
      return { color: "green", label: "HIGH" };
    case "medium":
      return { color: "yellow", label: "MEDIUM" };
    default:
      return { color: "red", label: "LOW" };
  }
}


export function errorToColor(error: number | null) {
  if (error == null) return "#adb5bd"; // gray = missing data
  return echarts.color.lerp(
    Math.min(error / 0.1, 1), // clamp (0–10% error)
    ["#2f9e44", "#f03e3e"]
  );
}

export function errorToWidth(error: number | null) {
  if (error == null) return 1;
  return 1 + Math.min(error * 40, 6);
}
