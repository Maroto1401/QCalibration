// Embedding visualization - displays logical to physical qubit mapping on topology
import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { Stack, Text, Box, Paper, Badge, Group, Modal } from "@mantine/core";
import { Topology, TranspilationResult } from "../../types";
import { errorToColor, errorToWidth, computeHeavyHexPositions } from "../../utils/functions";

interface Props {
  topology: Topology;
  embedding: TranspilationResult['embedding'] | null;
  opened: boolean;
  onClose: () => void;
  algorithmName?: string;
}

function isValidError(error: number | null | undefined): boolean {
  return error !== null && error !== undefined && error < 1.0 && error >= 0;
}

export function EmbeddingVisualization({ topology, embedding, opened, onClose, algorithmName }: Props) {
  const option = useMemo(() => {
    if (!topology.calibrationData || !embedding) return {};

    const { qubits, gates } = topology.calibrationData;

    // Create inverse mapping: physical qubit -> logical qubit(s)
    const physicalToLogical = new Map<number, number[]>();
    Object.entries(embedding).forEach(([logical, physical]) => {
      const logicalNum = parseInt(logical);
      const physicalNum = physical as number;
      if (!physicalToLogical.has(physicalNum)) {
        physicalToLogical.set(physicalNum, []);
      }
      physicalToLogical.get(physicalNum)!.push(logicalNum);
    });

    const qubitMap = new Map(qubits.map((q) => [q.qubit, q]));

    const gateMap = new Map<string, { error: number | null }>();
    gates
      .filter((g) => g.name === "cz" && g.qubits.length === 2)
      .forEach((g) => {
        const key1 = `${g.qubits[0]}-${g.qubits[1]}`;
        const key2 = `${g.qubits[1]}-${g.qubits[0]}`;
        const valid = isValidError(g.gate_error);
        gateMap.set(key1, { error: valid ? g.gate_error! : null });
        gateMap.set(key2, { error: valid ? g.gate_error! : null });
      });

    const positions =
      topology.topology_layout === "heavy-hex"
        ? computeHeavyHexPositions(topology.numQubits)
        : null;

    const nodes = Array.from({ length: topology.numQubits }).map((_, i) => {
      const q = qubitMap.get(i);
      const readoutError = q?.readout_error;
      const validReadout = isValidError(readoutError);
      const pos = positions?.[i];
      
      const logicalQubits = physicalToLogical.get(i) || [];
      const isUsed = logicalQubits.length > 0;

      return {
        id: String(i),
        name: String(i),
        symbolSize: isUsed ? 35 : 25,
        x: pos?.x,
        y: pos?.y,
        itemStyle: { 
          color: isUsed 
            ? '#228be6'
            : validReadout 
            ? errorToColor(readoutError ?? null) 
            : '#95a5a6',
          borderColor: isUsed ? '#1971c2' : '#fff',
          borderWidth: isUsed ? 3 : 2,
          shadowBlur: isUsed ? 10 : 3,
          shadowColor: isUsed ? 'rgba(34, 139, 230, 0.6)' : 'rgba(0,0,0,0.15)',
        },
        label: {
          show: true,
          color: '#fff',
          fontWeight: isUsed ? 'bold' : 'normal',
          fontSize: isUsed ? 13 : 12,
          formatter: isUsed 
            ? `P${i}\nL${logicalQubits.join(',')}` 
            : '{b}',
          lineHeight: 16,
        },
        value: validReadout ? readoutError : null,
        logicalQubits,
        isUsed,
      };
    });

    const addedEdges = new Set<string>();
    const links = topology.coupling_map
      .map(([a, b]) => {
        const key = a < b ? `${a}-${b}` : `${b}-${a}`;
        if (addedEdges.has(key)) return null;
        addedEdges.add(key);

        const gateInfo = gateMap.get(key);
        const error = gateInfo?.error ?? null;
        const validError = isValidError(error);

        const aUsed = physicalToLogical.has(a);
        const bUsed = physicalToLogical.has(b);
        const isUsed = aUsed && bUsed;

        return {
          source: String(a),
          target: String(b),
          lineStyle: {
            color: isUsed 
              ? '#228be6' 
              : validError 
              ? errorToColor(error) 
              : '#95a5a6',
            width: isUsed 
              ? 5 
              : validError 
              ? errorToWidth(error) 
              : 2,
            type: "solid",
            opacity: isUsed ? 0.85 : 0.25,
          },
          emphasis: {
            lineStyle: {
              width: isUsed ? 7 : validError ? errorToWidth(error) * 1.5 : 3,
              opacity: 1,
            },
          },
          value: error,
          validError,
          isUsed,
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
            const logicalQubits = params.data.logicalQubits;
            const isUsed = params.data.isUsed;
            
            if (!q) return "No calibration data";
            
            const readoutError = q.readout_error;
            const validReadout = isValidError(readoutError);
            
            return `
              <div style="padding: 6px;">
                <b style="font-size: 14px;">Physical Qubit ${q.qubit}</b><br/>
                ${isUsed ? `<span style="color: #228be6; font-weight: bold;">→ Logical Qubit(s): ${logicalQubits.join(', ')}</span><br/><br/>` : ''}
                <span style="color: #666;">T1:</span> <b>${q.t1 != null ? (q.t1 * 1e6).toFixed(2) : "–"} µs</b><br/>
                <span style="color: #666;">T2:</span> <b>${q.t2 != null ? (q.t2 * 1e6).toFixed(2) : "–"} µs</b><br/>
                <span style="color: #666;">Frequency:</span> <b>${q.frequency?.toFixed(3) ?? "–"} GHz</b><br/>
                <span style="color: #666;">Readout error:</span> <b>${validReadout ? ((readoutError ?? 0) * 100).toFixed(3) + '%' : 'N/A'}</b>
              </div>
            `;
          }
          if (params.dataType === "edge") {
            const error = params.data.value;
            const validError = params.data.validError;
            const isUsed = params.data.isUsed;
            const errorPercent = validError ? (error * 100).toFixed(3) + '%' : 'N/A';
            
            return `
              <div style="padding: 6px;">
                <b style="font-size: 14px;">CZ Gate</b><br/>
                <span style="color: #666;">Physical Qubits ${params.data.source} ↔ ${params.data.target}</span><br/>
                ${isUsed ? '<span style="color: #228be6; font-weight: bold;">✓ Used in embedding</span><br/>' : ''}
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
          roam: true,
          draggable: true,
          scaleLimit: { min: 0.15, max: 3 },
          label: { 
            show: true, 
            position: "inside",
          },
          emphasis: {
            focus: "adjacency",
            label: { 
              show: true, 
              fontWeight: "bold",
              fontSize: 15,
            },
            itemStyle: {
              borderWidth: 4,
            }
          },
          data: nodes,
          links,
          animation: true,
          animationDuration: 1500,
          animationEasingUpdate: "cubicOut",
          zoom: 1.2,
          center: ['50%', '50%'],
        },
      ],
    };
  }, [topology, embedding]);

  const embeddingStats = useMemo(() => {
    if (!embedding) return null;
    
    const entries = Object.entries(embedding);
    const physicalQubits = new Set(entries.map(([_, p]) => p as number));
    
    return {
      logicalQubits: entries.length,
      physicalQubits: physicalQubits.size,
      utilizationRate: ((physicalQubits.size / topology.numQubits) * 100).toFixed(1),
    };
  }, [embedding, topology]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="95%"
      title={
        <div>
          <Text fw={700} size="lg">Embedding Visualization</Text>
          {algorithmName && (
            <Text size="sm" c="dimmed">Algorithm: {algorithmName.toUpperCase()}</Text>
          )}
        </div>
      }
    >
      {!embedding ? (
        <Text c="dimmed" ta="center" py="xl">No embedding data available</Text>
      ) : (
        <Stack gap="md" style={{ height: '80vh' }}>
          <Paper p="sm" withBorder>
          <Group justify="space-between">
            <div>
              <Text size="sm" fw={600}>Embedding Summary</Text>
              <Text size="xs" c="dimmed">
                Blue nodes and edges show the logical circuit mapped to physical qubits
              </Text>
            </div>
            {embeddingStats && (
              <Group gap="md">
                <div>
                  <Text size="xs" c="dimmed">Logical Qubits</Text>
                  <Badge size="lg" variant="light">{embeddingStats.logicalQubits}</Badge>
                </div>
                <div>
                  <Text size="xs" c="dimmed">Physical Qubits Used</Text>
                  <Badge size="lg" variant="light" color="blue">{embeddingStats.physicalQubits}</Badge>
                </div>
                <div>
                  <Text size="xs" c="dimmed">Utilization</Text>
                  <Badge size="lg" variant="light" color="cyan">{embeddingStats.utilizationRate}%</Badge>
                </div>
              </Group>
            )}
          </Group>
        </Paper>

        <Box style={{ flex: 1, minHeight: 0, position: "relative" }}>
          <Paper
            shadow="sm"
            p="xs"
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              zIndex: 10,
              width: 200,
              background: "rgba(255, 255, 255, 0.95)",
              backdropFilter: "blur(10px)",
            }}
          >
            <Stack gap="xs">
              <div>
                <Text size="xs" fw={600} mb={6}>Legend</Text>
                <Group gap="xs" mb={6}>
                  <Box
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      background: '#228be6',
                      border: '3px solid #1971c2',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 9,
                      color: '#fff',
                      fontWeight: 'bold',
                    }}
                  >
                    P0
                  </Box>
                  <div style={{ flex: 1 }}>
                    <Text size="xs" fw={500}>Used in embedding</Text>
                    <Text size="xs" c="dimmed">P = Physical, L = Logical</Text>
                  </div>
                </Group>
                <Group gap="xs" mb={8}>
                  <Box
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      background: '#95a5a6',
                      border: '2px solid #fff',
                    }}
                  />
                  <Text size="xs">Unused physical qubit</Text>
                </Group>
                <Group gap="xs" mb={4}>
                  <Box
                    style={{
                      width: 40,
                      height: 4,
                      background: '#228be6',
                      borderRadius: 2,
                    }}
                  />
                  <Text size="xs">Active connection</Text>
                </Group>
                <Group gap="xs">
                  <Box
                    style={{
                      width: 40,
                      height: 2,
                      background: '#95a5a6',
                      borderRadius: 1,
                      opacity: 0.4,
                    }}
                  />
                  <Text size="xs">Unused connection</Text>
                </Group>
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
          Drag nodes • Scroll to zoom • Hover for qubit details and mapping
        </Text>
      </Stack>
      )}
    </Modal>
  );
}