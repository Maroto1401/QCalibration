import { Container, Title, Text, Card, Badge, SimpleGrid, Group, ThemeIcon } from "@mantine/core";
import { FC } from "react";
import {
  IconUpload,
  IconChartBar,
  IconNetwork,
  IconCpu,
  IconFileExport,
} from "@tabler/icons-react";

interface WorkflowStep {
  icon: FC<any>;
  title: string;
  description: string;
  color: string;
}

const workflowSteps: WorkflowStep[] = [
  {
    icon: IconUpload,
    title: "Upload Circuit",
    description: "Start by uploading your OpenQASM2 quantum circuit file",
    color: "blue",
  },
  {
    icon: IconChartBar,
    title: "Analyze",
    description: "Visualize circuit features and explore gate distribution",
    color: "cyan",
  },
  {
    icon: IconNetwork,
    title: "Select Hardware",
    description: "Choose from real IBM quantum processor topologies with live calibration data",
    color: "grape",
  },
  {
    icon: IconCpu,
    title: "Transpile",
    description: "Apply routing algorithms (Naive, Dynamic, SABRE) optimized for your hardware",
    color: "violet",
  },
  {
    icon: IconChartBar,
    title: "Optimize",
    description: "Analyze error estimates, depth, and gate counts with calibration-aware metrics",
    color: "indigo",
  },
  {
    icon: IconFileExport,
    title: "Export",
    description: "Download your optimized circuit and qubit embedding as OpenQASM2",
    color: "teal",
  },
];

export function WorkflowSection() {
  return (
    <Container size="md" style={{ paddingBottom: 40 }}>
      <div style={{ marginBottom: 24 }}>
        <Title order={2} fw={600} size="h3" mb="sm">
          How QCal Works
        </Title>
        <Text c="dimmed">
          A six-step journey from circuit upload to hardware-optimized implementation
        </Text>
      </div>

      <SimpleGrid
        cols={{ base: 1, sm: 2, md: 3 }}
        spacing="md"
      >
        {workflowSteps.map((step, index) => {
          const Icon = step.icon;
          return (
            <Card 
              key={step.title} 
              withBorder 
              radius="md" 
              p="lg"
              style={{
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = "0 12px 24px rgba(0, 0, 0, 0.08)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.12)";
              }}
            >
              <Group justify="space-between" mb="md">
                <ThemeIcon
                  size="lg"
                  radius="md"
                  variant="light"
                  color={step.color}
                >
                  <Icon size={24} stroke={1.5} />
                </ThemeIcon>
                <Badge
                  size="lg"
                  variant="gradient"
                  gradient={{ from: step.color, to: "dark", deg: 90 }}
                >
                  {index + 1}
                </Badge>
              </Group>
              <Title order={4} fw={600} mb="xs">
                {step.title}
              </Title>
              <Text size="sm" c="dimmed" lh={1.5}>
                {step.description}
              </Text>
            </Card>
          );
        })}
      </SimpleGrid>
    </Container>
  );
}