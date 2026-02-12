// Topology page - select and view quantum hardware topologies
import { useEffect, useState } from "react";
import { Container, Text, Loader, Center } from "@mantine/core";
import TopologySelector from "../components/topologyComponents/TopologySelector";
import { Topology, CircuitData } from "../types";
import { useLocation } from "react-router-dom";

export default function TopologyPage() {
  const [topologies, setTopologies] = useState<Topology[]>([]);
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
      const list = Object.values(raw) as Topology[];
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

  const location = useLocation();
  const { circuit } = location.state as { circuit: CircuitData };
  const handleSelectTopology = (topologyId: string) => {
    setSelectedTopology(topologyId);
    console.log("Selected topology:", topologyId);
  };
  return (
    <Container size="lg" py="xl">

      {loading && (
  <Center style={{ flexDirection: "column", gap: 8 }}>
    <Loader size="lg" />
    <Text size="sm" color="dimmed">
      Loading topologies, please wait a moment...
    </Text>
  </Center>
)}


      {error && <Text>{error}</Text>}

      {!loading && !error && !selectedTopology && (
  <>
    {topologies.length > 0 ? (
      <TopologySelector topologies={topologies} circuit={circuit} onSelect={handleSelectTopology} />
    ) : (
      <Text mt="xl">
        No topologies available.
      </Text>
    )}
  </>
)}
    </Container>
  );
}
