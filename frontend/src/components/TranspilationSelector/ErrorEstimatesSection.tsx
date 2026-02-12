// Error estimates section - displays calibration and error information
import { Container, Paper, Group, ThemeIcon, Title, Text } from "@mantine/core";
import { IconBulb } from "@tabler/icons-react";

export function ErrorEstimatesSection() {
  return (
    <Container size="md" style={{ paddingBottom: 40 }}>
      <Paper
        radius="md"
        p="lg"
        style={{
          background: "linear-gradient(135deg, rgba(255, 159, 64, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%)",
          border: `1px solid rgba(255, 193, 7, 0.2)`,
        }}
      >
        <Group mb="md">
          <ThemeIcon size="lg" radius="md" variant="light" color="orange">
            <IconBulb size={24} stroke={1.5} />
          </ThemeIcon>
          <Title order={4} fw={600}>
            Understanding Error Estimates
          </Title>
        </Group>
        <Text size="sm" c="dimmed" lh={1.6}>
          All error estimates (readout, gate, decoherence) are <strong>approximations</strong> based on 
          hardware calibration data. They provide valuable guidance for algorithm selection and optimization, 
          but actual execution results may vary due to environmental factors and quantum noise characteristics. 
          Use these metrics as a compass, not an absolute predictor.
        </Text>
      </Paper>
    </Container>
  );
}