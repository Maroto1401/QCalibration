import { useLocation, useNavigate } from "react-router-dom";
import { Button, Container, Text, Tabs } from "@mantine/core";
import { Topology } from "../../types";
import { TopologyHeader } from "./TopologyHeader";
import { TopologyConnectivityMap } from "./TopologyConnectivityMap";

interface TopologyViewProps {
  topology: Topology;
}

export default function TopologyView() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as TopologyViewProps | null;

  if (!state?.topology) {
    // Safety fallback (refresh / direct URL access)
    return (
      <>
        <Text>No topology data provided.</Text>
        <Button onClick={() => navigate(-1)}>Go back</Button>
      </>
    );
  }

  const { topology } = state;

  return (
    <Container size="lg" py="md">
    <TopologyHeader topology={topology} />
    <Tabs defaultValue="connectivity">
  <Tabs.List>
    <Tabs.Tab value="connectivity">Connectivity</Tabs.Tab>
    <Tabs.Tab value="details">Details</Tabs.Tab>
  </Tabs.List>

  <Tabs.Panel value="connectivity" pt="md" style={{ height: 'calc(150vh - 200px)' }}>
    <TopologyConnectivityMap topology={topology} />
  </Tabs.Panel>
</Tabs>
    </Container>
  );
}


