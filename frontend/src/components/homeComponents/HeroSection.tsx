// Hero section - landing banner with app title and CTA
import { Container, Title, Group, Stack } from "@mantine/core";
import { IconCircuitResistor } from "@tabler/icons-react";
import { CircuitMetadata } from "../../types";

interface HeroSectionProps {
  setCircuitMetadata: (m: CircuitMetadata) => void;
}

export function HeroSection({ setCircuitMetadata }: HeroSectionProps) {
  return (
    <Container size="md" style={{ paddingTop: 36, paddingBottom: 40 }}>
      <Group justify="center" align="center" gap="xs">
        <IconCircuitResistor size={32} stroke={1.5} color="#228BE6" />
        <Stack gap={0}>
          <Title 
            order={2}
            fw={700}
            style={{
              background: "linear-gradient(45deg, #228BE6 0%, #15AABF 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            QCal - Take your Quantum Circuits to the Next Level
          </Title>
        </Stack>
      </Group>
      
    </Container>
  );
}