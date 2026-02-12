// Topology connectivity map - visualizes qubit layout and coupling map on hardware
import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { Stack, Text, Box, Paper, Badge, Group } from "@mantine/core";
import { Topology } from "../../types";
import { errorToColor, errorToWidth, computeHeavyHexPositions } from "../../utils/functions";
import { ErrorOneNote } from "./TopologyOneErrorRate";
import { SegmentedControl, Slider } from "@mantine/core";
import { useState } from "react";

interface Props {
  topology: Topology;
}

type EdgeStatus = "all" | "available" | "obsolete";

function isObsoleteError(error: number | null | undefined): boolean {
  return error === 1;
}
// Filter out invalid error rates (1.0 means gate not operational)
function isValidError(error: number | null | undefined): boolean {
  return error !== null && error !== undefined && error < 1.0 && error >= 0;
}

export function TopologyConnectivityMap({ topology }: Props) {
    const [edgeStatus, setEdgeStatus] =
    useState<"all" | "available" | "obsolete">("all");

  const [maxError, setMaxError] = useState(0.05);

  const option = useMemo(() => {
    if (!topology.calibrationData) return {};

    const { qubits, gates } = topology.calibrationData;

    // --- Qubit calibration lookup
    const qubitMap = new Map(qubits.map((q) => [q.qubit, q]));

    // --- Gate calibration lookup (CZ gates)
    const gateMap = new Map<
  string,
  { error: number | null; obsolete: boolean }
>();

    gates
    .filter((g) => g.name === "cz" && g.qubits.length === 2)
    .forEach((g) => {
        const key1 = `${g.qubits[0]}-${g.qubits[1]}`;
        const key2 = `${g.qubits[1]}-${g.qubits[0]}`;

        const obsolete = isObsoleteError(g.gate_error);
        const valid = isValidError(g.gate_error);

        gateMap.set(key1, {
        error: valid ? g.gate_error! : null,
        obsolete,
        });
        gateMap.set(key2, {
        error: valid ? g.gate_error! : null,
        obsolete,
        });
    });


    const positions =
    topology.topology_layout === "heavy-hex"
        ? computeHeavyHexPositions(topology.numQubits)
        : null;

    const nodes = Array.from({ length: topology.numQubits }).map((_, i) => {
    const q = qubitMap.get(i);
    const readoutError = q?.readout_error;
    const validReadout = isValidError(readoutError);
    const pos = positions?.[i]

      
      return {
        id: String(i),
        name: String(i),
        symbolSize: 30,
        x: pos?.x,
        y: pos?.y,
        itemStyle: { 
          color: validReadout ? errorToColor(readoutError ?? null) : '#95a5a6',
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 3,
          shadowColor: 'rgba(0,0,0,0.15)',
        },
        label: {
          show: true,
          color: '#fff',
          fontWeight: 'bold',
          fontSize: 12,
          formatter: '{b}',
        },
        value: validReadout ? readoutError : null,
      };
    });

    // --- Edges (remove duplicates)
    const addedEdges = new Set<string>();
    const links = topology.coupling_map
      .map(([a, b]) => {
        const key = a < b ? `${a}-${b}` : `${b}-${a}`;
        if (addedEdges.has(key)) return null;
        addedEdges.add(key);

        const gateInfo = gateMap.get(key);
        const error = gateInfo?.error ?? null;
        const obsolete = gateInfo?.obsolete ?? false;
        const validError = isValidError(error);

        // --- FILTERING ---
        if (edgeStatus === "available" && !validError) return null;
        if (edgeStatus === "obsolete" && !obsolete) return null;

        // Slider filter (applies only to valid edges)
        if (validError && error! > maxError) return null;
        
        return {
          source: String(a),
          target: String(b),
          lineStyle: {
            color: obsolete
            ? "#000"
            : validError
            ? errorToColor(error)
            : "#95a5a6",
            width: validError
                ? errorToWidth(error)
                : obsolete
                ? 1.5
                : 2,
            type: obsolete ? "dashed" : "solid",
            opacity: obsolete ? 0.6 : validError ? 0.7 : 0.3,
            },

          emphasis: {
            lineStyle: {
                width: obsolete
                ? 2
                : validError
                    ? errorToWidth(error) * 1.5
                    : 3,
                opacity: 1,
            },
            },

          value: error,
          validError,
        };
      })
      .filter(Boolean);

    return {
      tooltip: {
        trigger: "item",
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ccc',
        borderWidth: 1,
        textStyle: {
          color: '#333',
        },
        formatter: (params: any) => {
          if (params.dataType === "node") {
            const q = qubitMap.get(Number(params.data.id));
            if (!q) return "No calibration data";
            const readoutError = q.readout_error;
            const validReadout = isValidError(readoutError);
            return `
              <div style="padding: 4px;">
                <b style={{ fontSize: 14 }}>Qubit ${q.qubit}</b><br/>
                <span style={{ color: "#666" }}>T1:</span>${" "}
                <b>${q.t1 != null ? (q.t1 * 1e6).toFixed(2) : "–"} µs</b><br/>
                <span style={{ color: "#666" }}>T2:</span>${" "}
                <b>${q.t2 != null ? (q.t2 * 1e6).toFixed(2) : "–"} µs</b><br/>

                <span style="color: #666;">Frequency:</span> <b>${q.frequency?.toFixed(3) ?? "–"} GHz</b><br/>
                <span style="color: #666;">Readout error:</span> <b>${validReadout ? ((readoutError ?? 0) * 100).toFixed(3) + '%' : 'N/A'}</b>
              </div>
            `;
          }
          if (params.dataType === "edge") {
            const error = params.data.value;
            const validError = params.data.validError;
            const errorPercent = validError ? (error * 100).toFixed(3) + '%' : 'N/A';
            return `
              <div style="padding: 4px;">
                <b style="font-size: 14px;">CZ Gate</b><br/>
                <span style="color: #666;">Qubits ${params.data.source} ↔ ${params.data.target}</span><br/>
                <span style="color: #666;">Error rate:</span> <b>${errorPercent}</b>
                ${!validError ? '<br/><span style="color: #e03131; font-size: 11px;">⚠ Gate not operational</span>' : ''}
              </div>
            `;
          }
        },
      },
      series: [
        {
          type: "graph",
          layout: "none",
          force: {
            repulsion: 2000,
            edgeLength: [150, 250],
            gravity: 0.05,
            friction: 0.6,
            layoutAnimation: true,
          },
          roam: true,
          draggable: true,
          scaleLimit: { min: 0.15, max: 3 },
          label: { 
            show: true, 
            position: "inside",
            formatter: '{b}',
          },
          emphasis: {
            focus: "adjacency",
            label: { 
              show: true, 
              fontWeight: "bold",
              fontSize: 14,
            },
            itemStyle: {
              borderWidth: 3,
            }
          },
          data: nodes,
          links,
          animation: true,
          animationDuration: 1500,
          animationEasingUpdate: "cubicOut",
          zoom: 1.2,
          center: ['60%', '50%'],
        },
      ],
    };
  }, [topology, edgeStatus, maxError]);

  // Calculate statistics for CZ gates only
  const czStats = useMemo(() => {
    if (!topology.calibrationData) return null;
    
    const { gates } = topology.calibrationData;
    const czGates = gates.filter((g) => g.name === "cz" && g.qubits.length === 2);
    
    if (czGates.length === 0) return null;

    const validErrors = czGates
      .map(g => g.gate_error)
      .filter(e => isValidError(e)) as number[];
    
    if (validErrors.length === 0) return null;

    const avgError = validErrors.reduce((sum, e) => sum + e, 0) / validErrors.length;
    const minError = Math.min(...validErrors);
    const maxError = Math.max(...validErrors);

    return {
      avg: avgError,
      min: minError,
      max: maxError,
      count: validErrors.length,
      total: czGates.length,
    };
  }, [topology]);

  // Calculate statistics for CX gates
  const cxStats = useMemo(() => {
    if (!topology.calibrationData) return null;
    
    const { gates } = topology.calibrationData;
    const cxGates = gates.filter((g) => g.name === "cx" && g.qubits.length === 2);
    
    if (cxGates.length === 0) return null;

    const validErrors = cxGates
      .map(g => g.gate_error)
      .filter(e => isValidError(e)) as number[];
    
    if (validErrors.length === 0) return null;

    const avgError = validErrors.reduce((sum, e) => sum + e, 0) / validErrors.length;
    const minError = Math.min(...validErrors);
    const maxError = Math.max(...validErrors);

    return {
      avg: avgError,
      min: minError,
      max: maxError,
      count: validErrors.length,
      total: cxGates.length,
    };
  }, [topology]);

  return (
    <Stack gap="md" style={{ height: '100%' }}>
      <Group justify="space-between" align="center">
        <div>
          <Text fw={600} size="lg">Connectivity Map</Text>
          <Text size="xs" c="dimmed">{topology.numQubits} qubits, {topology.coupling_map.length} connections</Text>
        </div>
        <Group align="flex-start">
  <Text size="s"  mt={2}>
    Gate Filter:
  </Text>
        <Stack gap={6}>
  <SegmentedControl
    size="xs"
    value={edgeStatus}
    onChange={(v) => setEdgeStatus(v as EdgeStatus)}
    data={[
      { label: "All", value: "all" },
      { label: "Available", value: "available" },
      { label: "Obsolete", value: "obsolete" },
    ]}
  />

  <Slider
    size="xs"
    min={0}
    max={1}
    step={0.001}
    value={maxError}
    onChange={setMaxError}
    label={(v) => `${(v * 100).toFixed(2)}%`}
    disabled={edgeStatus === "obsolete"}
  />
</Stack>
</Group>
      </Group>

      <Box style={{ flex: 1, minHeight: 0, position: "relative" }}>
        {/* Compact Legend */}
        <Paper
          shadow="sm"
          p="xs"
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            zIndex: 10,
            width: 160,
            background: "rgba(255, 255, 255, 0.95)",
            backdropFilter: "blur(10px)",
          }}
        >
          <Stack gap="xs">
            <div>
              <Text size="xs" fw={600} mb={3}>Nodes</Text>
              <Text size="xs" c="dimmed" mb={4}>Readout error</Text>
              <Box
                style={{
                  height: 5,
                  width: "100%",
                  borderRadius: 2,
                  background: "linear-gradient(90deg, #2f9e44, #fab005, #f03e3e)",
                }}
              />
              <Group justify="space-between" mt={2}>
                <Text size="xs" c="dimmed">Low</Text>
                <Text size="xs" c="dimmed">High</Text>
              </Group>
            </div>

            <div style={{ marginTop: 8 }}>
              <Text size="xs" fw={600} mb={3}>Edges</Text>
              <Text size="xs" c="dimmed">CZ gate error</Text>
              <Text size="xs" c="dimmed">Color and width represents error</Text>
              {czStats && (
            <Stack gap={4}>
              <Text size="xs" fw={600}>CZ Gates Errors Stats</Text>
              <Text size="xs" c="dimmed">{czStats.count}/{czStats.total} calibrated</Text>
              <Group justify="apart" gap="xs">
                <Text size="xs" c="dimmed">Avg:</Text>
                <Badge size="sm" variant="light">{(czStats.avg * 100).toFixed(3)}%</Badge>
              </Group>
              <Group justify="apart" gap="xs">
                <Text size="xs" c="dimmed">Best:</Text>
                <Badge size="sm" variant="light" color="green">{(czStats.min * 100).toFixed(3)}%</Badge>
              </Group>
              <Group justify="apart" gap="xs">
                <Text size="xs" c="dimmed">Worst:</Text>
                <Badge size="sm" variant="light" color="red">{(czStats.max * 100).toFixed(3)}%</Badge>
              </Group>
            </Stack>
        )}
            </div>
          </Stack>
        </Paper>

        <ReactECharts
          option={option}
          style={{ height: "100%", width: "100%" }}
          opts={{ renderer: "canvas" }}
          notMerge={true}
        />
      </Box>

    
      <Text size="xs" c="dimmed" ta="center">
        Drag nodes • Scroll to zoom • Hover for details • Black-Dashed line = not calibrated
      </Text>
      <ErrorOneNote></ErrorOneNote>
    </Stack>

  );
}

