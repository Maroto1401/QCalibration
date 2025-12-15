import { useLocation, useNavigate } from "react-router-dom";
import { Button, Container, Text, Box } from "@mantine/core";
import { CircuitData, Topology } from "../../types";
import { TopologyHeader } from "./TopologyHeader";
import { TopologyConnectivityMap } from "./TopologyConnectivityMap";

interface TopologyViewProps {
  topology: Topology;
  circuit: CircuitData
}

export default function TopologyView() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as TopologyViewProps | null;

  const goToTranspilationSelector = () => {
    if (!state?.topology) return;
    navigate("/transpilation-selector", { state: { topology } });
  };

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

  <Box style={{ height: 'calc(150vh - 200px)', marginBottom: 24 }}>
    <TopologyConnectivityMap topology={topology} />
  </Box>

  <Box style={{ display: 'flex', justifyContent: 'center', marginTop: 16 }}>
    <Button
      radius="xl"
      size="lg" // slightly smaller than xl
      onClick={goToTranspilationSelector}
      style={{
        width: 600, 
        backgroundImage: 'linear-gradient(45deg, #1E90FF, #00BFFF)',
        color: 'white',
        fontSize: 16,
        fontWeight: 700,
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      styles={{
        root: {
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: '0 15px 35px rgba(0,0,0,0.3)',
          },
        },
      }}
    >
      Select Topology for Transpilation
    </Button>
  </Box>
</Container>
  );  
}


