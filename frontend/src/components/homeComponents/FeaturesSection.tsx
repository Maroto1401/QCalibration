import { Container, Title, Text, Card, SimpleGrid, Group, ThemeIcon } from "@mantine/core";
import { FC } from "react";
import {
  IconNetwork,
  IconCpu,
  IconChartBar,
  IconFileExport,
} from "@tabler/icons-react";

interface Feature {
  icon: FC<any>;
  title: string;
  description: string;
  color: string;
}

const features: Feature[] = [
  {
    icon: IconNetwork,
    title: "Real Hardware Topologies",
    description: "Access live IBM quantum processor architectures with current calibration data. Understand exact connectivity constraints before transpilation.",
    color: "blue",
  },
  {
    icon: IconCpu,
    title: "Multiple Routing Algorithms",
    description: "Compare Naive, Dynamic, and SABRE algorithms. Our calibration-aware SABRE variant considers gate error rates to minimize execution fidelity loss.",
    color: "grape",
  },
  {
    icon: IconChartBar,
    title: "Comprehensive Error Analysis",
    description: "Estimate readout errors, gate errors, and decoherence effects based on real hardware calibration. These are approximations that help guide optimization.",
    color: "cyan",
  },
  {
    icon: IconFileExport,
    title: "Seamless Export",
    description: "Export optimized circuits in OpenQASM2 format along with qubit embeddings. Ready to submit to your chosen quantum backend.",
    color: "teal",
  },
];

export function FeaturesSection() {
  return (
    <Container size="md" style={{ paddingBottom: 40 }}>
      <div style={{ marginBottom: 24 }}>
        <Title order={2} fw={600} size="h3" mb="sm">
          Intelligent Optimization Features
        </Title>
        <Text c="dimmed">
          QCal leverages real hardware data to guide your optimization decisions
        </Text>
      </div>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card 
              key={feature.title} 
              withBorder 
              radius="md" 
              p="lg"
              style={{
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 8px 16px rgba(34, 139, 230, 0.12)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.12)";
              }}
            >
              <Group mb="md">
                <ThemeIcon size="lg" radius="md" variant="light" color={feature.color}>
                  <Icon size={24} stroke={1.5} />
                </ThemeIcon>
                <Title order={4} fw={600}>
                  {feature.title}
                </Title>
              </Group>
              <Text size="sm" c="dimmed" lh={1.6}>
                {feature.description}
              </Text>
            </Card>
          );
        })}
      </SimpleGrid>
    </Container>
  );
}