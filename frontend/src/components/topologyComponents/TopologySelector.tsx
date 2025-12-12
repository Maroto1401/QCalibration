import { useState } from "react";
import {
  Container,
  Title,
  Stack,
  Grid,
  TextInput,
  Divider,
} from "@mantine/core";
import { IconNetwork, IconSearch } from "@tabler/icons-react";
import { TopologyCard as TopologyCardType } from "../../types";
import TopologyCard from "./TopologyCard"; // import the card component

interface TopologySelectorProps {
  topologies: TopologyCardType[];
  onSelect: (topologyId: string) => void;
}

export default function TopologySelector({ topologies, onSelect }: TopologySelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");

  // Filter topologies by search query (name or vendor)
  const filteredTopologies = topologies.filter(
    (t) =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.vendor.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group by vendor
  const groupedByVendor = filteredTopologies.reduce<Record<string, TopologyCardType[]>>(
    (acc, topo) => {
      if (!acc[topo.vendor]) acc[topo.vendor] = [];
      acc[topo.vendor].push(topo);
      return acc;
    },
    {}
  );

  return (
    <Container size="xl" py="xl">
      <Stack>
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 12,
            marginBottom: 16,
          }}
        >
          <IconNetwork size={36} stroke={1.5} color="#228BE6" />
          <Title
            order={1}
            styles={{
              root: {
                background: "linear-gradient(45deg, #228BE6 0%, #15AABF 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                fontWeight: 700,
              },
            }}
          >
            Select Quantum Topology
          </Title>
        </div>

        {/* Search Bar */}
        <TextInput
          placeholder="Search by name or vendor"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.currentTarget.value)}
          leftSection={<IconSearch size={16} />}
        />

        {/* Topology Grid by Vendor */}
        {Object.entries(groupedByVendor).map(([vendor, vendorTopologies]) => (
          <Stack key={vendor}>
            <Divider my="sm" label={vendor} labelPosition="center" />
            <Grid gutter="lg">
              {vendorTopologies.map((topology) => (
                <Grid.Col key={topology.id} span={{ base: 12, md: 6, lg: 4 }}>
                  <TopologyCard
                    topology={topology}
                    onSelect={onSelect}
                  />
                </Grid.Col>
              ))}
            </Grid>
          </Stack>
        ))}

        {filteredTopologies.length === 0 && (
          <Stack align="center" mt="xl">
            <div>No topologies found.</div>
          </Stack>
        )}
      </Stack>
    </Container>
  );
}
