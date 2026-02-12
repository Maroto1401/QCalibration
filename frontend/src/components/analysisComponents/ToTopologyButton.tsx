// To topology button - CTA to proceed to topology selection page
import { Button } from "@mantine/core";

interface TopologyButtonProps {
  onClick: () => void;
  label?: string;
}

export default function ToTopologyButton({ onClick, label = "Add a Topology!" }: TopologyButtonProps) {
  return (
    <Button
      fullWidth
      radius="xl"
      size="xl"
      onClick={onClick}
      style={{
        backgroundImage: 'linear-gradient(45deg, #1E90FF, #00BFFF)',
        color: 'white',
        fontSize: 18,
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
      {label}
    </Button>
  );
}