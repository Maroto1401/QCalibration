// Error note - displays information about gate error rates on topology
import { Box, Text, Anchor, Group } from "@mantine/core";
import { IconAlertTriangle } from "@tabler/icons-react";

export function ErrorOneNote() {
  return (
    <Box
      p="sm"
      style={(theme) => ({
        borderLeft: `4px solid ${theme.colors.yellow[6]}`,
        backgroundColor: theme.colors.yellow[0],
        borderRadius: theme.radius.sm,
      })}
    >
      <Group gap="xs" mb={4}>
        <IconAlertTriangle size={14} />
        <Text fw={500} size="sm">
          Important Note!
        </Text>
      </Group>

      <Text size="sm" c="dimmed">
        An error gate of 1 indicates obsolete benchmarking data. The error is undefined (not a real
        value of 1). Use this qubit or edge with caution.{" "}
        <Anchor
          href="https://quantum.cloud.ibm.com/docs/en/guides/qpu-information#calibration-data"
          target="_blank"
          rel="noopener noreferrer"
        >
          Docs
        </Anchor>
      </Text>
    </Box>
  );
}
