import React, { useState } from "react";
import { Container, SimpleGrid, Stack, Text, SegmentedControl, Button, Box, useMantineTheme } from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import { useLocation, useNavigate } from "react-router-dom";
import TopologyCard from "../components/topologyComponents/TopologyCard";
import CircuitCard from "../components/TranspilationSelector/CircuitSummaryCard";
import { CircuitData, Topology } from "../types";

interface TranspilerOption {
  label: string;
  description?: string;
  value: string;
}


export default function TranspilationSelector() {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useMantineTheme();
  const smallerScreen = useMediaQuery(`(max-width: ${theme.breakpoints.md}px)`);
  const [selectedTranspiler, setSelectedTranspiler] = useState<string | undefined>(undefined);

  const state = location.state as {
    topology: Topology;
    circuit: CircuitData;
  } | null;

  if (!state?.topology || !state?.circuit) {
    return (
      <Container>
        <Text>Missing circuit or topology data.</Text>
        <Button onClick={() => navigate(-1)}>Go back</Button>
      </Container>
    );
  }

  const { topology, circuit } = state;

  const transpilerOptions: TranspilerOption[] = [
    { label: "Transpiler A", description: "Optimized for depth", value: "transpilerA" },
    { label: "Transpiler B", description: "Optimized for fidelity", value: "transpilerB" },
  ];


  const handleStartTranspilation = () => {
    if (!selectedTranspiler) return;
    const option = transpilerOptions.find((t) => t.value === selectedTranspiler);
    navigate("/transpilation", {
      state: { circuit, topology, transpiler: option },
    });
  };

  return (
    <Container size="lg" py="md">
      {/* Top Cards */}
      <SimpleGrid cols={smallerScreen ? 1 : 2} spacing="md">
        <CircuitCard
          circuit={circuit}
          metadata={{ filename: "Uploaded Circuit", filetype: "qasm", circuit_id: circuit.circuit_id }}
        />
        <TopologyCard topology={topology} circuit={circuit}/>
      </SimpleGrid>

      {/* Transpiler selection */}
      <Stack mt="xl" align="center">
        <Text size="md" fw={600}>
          Select Transpiler Mode
        </Text>

        <SegmentedControl
          value={selectedTranspiler}
          onChange={setSelectedTranspiler}
          data={transpilerOptions.map((t) => ({
            value: t.value,
            label: t.label + (t.description ? ` – ${t.description}` : ""),
          }))}
          size="md"
        />

        <Box style={{ width: "200px" }}>
          <Button
            fullWidth
            onClick={handleStartTranspilation}
            disabled={!selectedTranspiler}
          >
            Start Transpilation
          </Button>
        </Box>
      </Stack>
    </Container>
  );
}

