// Home page - landing page with circuit uploader and features
import { Divider, Text } from "@mantine/core";
import { CircuitMetadata } from "../types";
import { HeroSection } from "../components/homeComponents/HeroSection";
import { SupportedGatesSection } from "../components/homeComponents/SupportedGatesSection";
import { WorkflowSection } from "../components/homeComponents/WorkflowSection";
import { FeaturesSection } from "../components/homeComponents/FeaturesSection";
import { FeedbackSection } from "../components/homeComponents/FeedbackSection";
import CircuitUploader from "../components/homeComponents/CircuitUploader";

export default function HomePage({
  setCircuitMetadata,
}: {
  setCircuitMetadata: (m: CircuitMetadata) => void;
}) {
  return (
    <div>
      <HeroSection setCircuitMetadata={setCircuitMetadata} />
      
      <Divider style={{ marginTop: 10, marginBottom: 10 }} />
      
      <WorkflowSection />
      
      <Divider style={{ marginTop: 20, marginBottom: 10 }} />
      
      <FeaturesSection />
      
      <Divider style={{ marginTop: 20, marginBottom: 10 }} />
      
      <Text ta="center"> 
        Upload a quantum circuit (OpenQASM2) to start optimizing
      </Text>

      <div style={{ marginTop: 20, marginBottom: 20 }}>
        <CircuitUploader setCircuitMetadata={setCircuitMetadata} />
      </div>

      <SupportedGatesSection />

      <Divider style={{ marginTop: 20, marginBottom: 10 }} />
      
      <FeedbackSection />
    </div>
  );
}