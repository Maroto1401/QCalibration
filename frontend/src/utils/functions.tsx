// Utility functions - helpers for rendering and formatting data
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

// IBM Heavy-Hex Topology (explicit support for 133 and 156 qubits)
export function computeHeavyHexPositions(n: number) {
  const dx = 50; // horizontal spacing
  const dy = 50; // vertical spacing

  if (n !== 133 && n !== 156) {
    throw new Error(`Unsupported heavy-hex size: ${n}`);
  }

  const evenRowQubits = n === 156 ? 16 : 15;
  const oddRowQubits = 4;

  const positions: { x: number; y: number }[] = [];

  let qubitIndex = 0;
  let row = 0;

  while (qubitIndex < n) {
    const y = row * dy;

    if (row % 2 === 0) {
      // ---------- EVEN ROW ----------
      for (let col = 0; col < evenRowQubits && qubitIndex < n; col++) {
        positions.push({
          x: col * dx,
          y,
        });
        qubitIndex++;
      }
    } else {
      // ---------- ODD ROW ----------
      let shiftCols = 0;

      if (n === 156) {
        // rows: 1,5,9,13,... → +3
        // rows: 3,7,11,...   → +1
        if (row % 4 === 1) shiftCols = 3;
        else if (row % 4 === 3) shiftCols = 1;
      }

      if (n === 133) {
        // rows: 3,7,11,... → +2
        if (row % 4 === 3) shiftCols = 2;
      }

      // Fixed odd-row anchor positions
      const baseCols = [0, 4, 8, 12];

      for (let i = 0; i < oddRowQubits && qubitIndex < n; i++) {
        positions.push({
          x: (baseCols[i] + shiftCols) * dx,
          y,
        });
        qubitIndex++;
      }
    }

    row++;
  }

  // ---------- Center layout ----------
  const xs = positions.map(p => p.x);
  const ys = positions.map(p => p.y);

  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;

  return positions.map(p => ({
    x: p.x - cx,
    y: p.y - cy,
  }));
}

