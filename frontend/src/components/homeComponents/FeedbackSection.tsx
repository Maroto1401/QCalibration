import { Container, Paper, Stack, ThemeIcon, Title, Text, Button } from "@mantine/core";
import { IconFlask, IconMail } from "@tabler/icons-react";

interface FeedbackSectionProps {
  email?: string;
}

export function FeedbackSection({ email = "dmarotos14@gmail.com" }: FeedbackSectionProps) {
  return (
    <Container size="md" style={{ paddingBottom: 60 }}>
      <Paper
        radius="md"
        p="lg"
        style={{
          background: "linear-gradient(135deg, rgba(103, 58, 183, 0.1) 0%, rgba(63, 81, 181, 0.1) 100%)",
          border: `1px solid rgba(103, 58, 183, 0.2)`,
        }}
      >
        <Stack gap="lg" align="center" style={{ textAlign: "center" }}>
          <ThemeIcon
            size="xl"
            radius="md"
            variant="light"
            color="indigo"
          >
            <IconFlask size={32} stroke={1.5} />
          </ThemeIcon>
          <div>
            <Title order={3} fw={600} mb="xs">
              Shape the Future of QCal
            </Title>
            <Text c="dimmed" mb="md">
              Have ideas for improvement? Found a bug? Want to suggest new features? 
              We'd love to hear from you!
            </Text>
          </div>
          <Button
            component="a"
            href={`mailto:${email}`}
            rightSection={<IconMail size={18} />}
            size="md"
            variant="gradient"
            gradient={{ from: "indigo", to: "blue", deg: 90 }}
          >
            Get in Touch
          </Button>
          <Text size="xs" c="dimmed">
            📧 Send feedback, bug reports, or feature requests directly via email
          </Text>
        </Stack>
      </Paper>
    </Container>
  );
}