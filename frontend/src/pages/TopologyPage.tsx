import { useEffect, useState } from "react";
import { Container, Title, Text, Loader, Center } from "@mantine/core";
import TopologySelector from "../components/topologyComponents/TopologySelector";
import { TopologyCard } from "../types";

export default function TopologyPage() {
  const [topologies, setTopologies] = useState<TopologyCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTopology, setSelectedTopology] = useState<string | null>(null);
  // Function to fetch topologies from backend
  const fetchTopologies = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/retrieve-topologies");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const raw = await response.json();
      const list = Object.values(raw) as TopologyCard[];
      setTopologies(list);
    } catch (err: any) {
      setError(err.message || "Failed to fetch topologies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopologies();
  }, []);
  console.log("Fetched topologies:", topologies);

  const handleSelectTopology = (topologyId: string) => {
    setSelectedTopology(topologyId);
    console.log("Selected topology:", topologyId);
  };
  return (
    <Container size="lg" py="xl">
      <Title order={2} mb="md">
        Quantum Circuit Topology
      </Title>

      <Text mb="lg">Visual representation and details of your topology.</Text>

      {loading && (
        <Center>
          <Loader size="lg" />
        </Center>
      )}

      {error && <Text>{error}</Text>}

      {!loading && !error && !selectedTopology && (
  <>
    {topologies.length > 0 ? (
      <TopologySelector topologies={topologies} onSelect={handleSelectTopology} />
    ) : (
      <Text mt="xl">
        No topologies available.
      </Text>
    )}
  </>
)}


      {selectedTopology && (
        <Text>
          Selected Topology ID: <strong>{selectedTopology}</strong>
        </Text>
      )}
    </Container>
  );
}
