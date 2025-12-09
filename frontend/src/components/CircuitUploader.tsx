import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  FileButton,
  Group,
  Progress,
  Stack,
  Text,
  ThemeIcon,
} from '@mantine/core';

import {
  IconUpload,
  IconCode,
  IconAlertTriangle,
  IconCircleCheck,
} from '@tabler/icons-react';

type Props = {
  accept?: string;
  onFile?: (parsed: any) => void;
};


export default function CircuitUploader({ accept = '.qasm,.qasm3,.json', onFile }: Props) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  // ---------------------------
  // BACKEND REQUEST
  // ---------------------------
  async function parse_file(file: File) {
    const form = new FormData();
    form.append("file", file);

    const response = await fetch("http://localhost:8000/parse-circuit", {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      throw new Error("Backend error parsing circuit");
    }

    return await response.json();
  }

  // ---------------------------
  // VALIDATION HELPERS
  // ---------------------------
  const detectByContent = (s: string) => {
    const first = s.trim().split(/\r?\n/).find((l) => l.trim()) || "";
    if (first.includes("OPENQASM 3")) return "qasm3";
    if (first.includes("OPENQASM 2")) return "qasm";
    if (s.trim().startsWith("{") || s.trim().startsWith("[")) return "json";
    return null;
  };

  const validateQasm = (s: string, version: "qasm" | "qasm3") => {
    const first = s.trim().split(/\r?\n/).find((l) => l.trim()) || "";
    if (!first.includes("OPENQASM")) return { valid: false, msg: "Missing OPENQASM header" };
    if (version === "qasm" && !first.includes("2")) return { valid: false, msg: "Expected OPENQASM 2" };
    if (version === "qasm3" && !first.includes("3")) return { valid: false, msg: "Expected OPENQASM 3" };
    return { valid: true, msg: "" };
  };

  const validateJson = (s: string) => {
    try {
      const obj = JSON.parse(s);
      if (typeof obj === "object") return { valid: true, msg: "" };
      return { valid: false, msg: "Invalid JSON structure" };
    } catch {
      return { valid: false, msg: "Invalid JSON" };
    }
  };

  // ---------------------------
  // MAIN FILE PROCESSING
  // ---------------------------
  const validateAndHandleFile = useCallback(async (file: File | null) => {
    if (!file) return;
    setError(null);
    setSuccess(false);
    setFileName(file.name);

    const text = await file.text();

    // Determine type
    const ext = file.name.split(".").pop()?.toLowerCase();
    const type =
      ext === "qasm" ? "qasm" :
      ext === "qasm3" ? "qasm3" :
      ext === "json" ? "json" :
      detectByContent(text);

    if (!type) {
      setError("Unsupported file type");
      return;
    }

    // Validate content
    let validation = { valid: false, msg: "" };
    if (type === "qasm" || type === "qasm3") validation = validateQasm(text, type);
    else if (type === "json") validation = validateJson(text);

    if (!validation.valid) {
      setError(validation.msg);
      return;
    }

    // Show progress
    setProgress(40);

    try {
      const parsed = await parse_file(file);
      if (onFile) onFile(parsed.circuit);


      setProgress(100);
      setSuccess(true);

      navigate("/circuit-analysis", {
        state: { circuit: parsed.circuit },
      });

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setProgress(null);
    }

  }, []);

  // ---------------------------
  // DROP HANDLING
  // ---------------------------
  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files?.[0];
      if (f) validateAndHandleFile(f);
    },
    [validateAndHandleFile]
  );

  // ---------------------------
  // UI
  // ---------------------------
  return (
    <Box style={{ maxWidth: 600, margin: "0 auto" }}>

      <Box
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        style={{
          border: `2px dashed ${
            dragging ? "#4c6ef5" : error ? "#fa5252" : success ? "#51cf66" : "#ccc"
          }`,
          borderRadius: 12,
          padding: 40,
          background: dragging ? "#edf2ff" : "#f8f9fa",
          textAlign: "center",
          transition: "0.2s",
        }}
      >
        <Stack align="center">
          <ThemeIcon size={64} variant="light" color={error ? "red" : success ? "green" : "blue"}>
            {error ? <IconAlertTriangle size={32}/> :
             success ? <IconCircleCheck size={32}/> :
             <IconUpload size={32}/>}
          </ThemeIcon>

          <Text size="lg">Upload your Quantum Circuit</Text>
          <Text size="sm" color="dimmed">Drag & drop or select a file</Text>

          {/* UPLOAD BUTTON */}
          <FileButton onChange={(file) => validateAndHandleFile(file)} accept={accept}>
            {(props) => (
              <Button
                {...props}
                leftSection={<IconUpload size={16} />}
                variant="gradient"
                gradient={{ from: "violet", to: "blue", deg: 45 }}
                size="md"
                radius="md"
              >
                Choose file
              </Button>
            )}
          </FileButton>

          <Group wrap='wrap' align="center">
             <Text size="xs">Supported formats:</Text> 
             {accept.split(',').map((fmt) => 
             (<Box key={fmt} style={
                {background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                color: 'white', 
                padding: '4px 12px', 
                marginRight: 8, 
                borderRadius: 4, 
                fontSize: 11, 
                fontWeight: 600, 
                fontFamily: 'monospace',
                textAlign: 'center', 
                whiteSpace: 'nowrap', 
                display: 'inline-block', 
                }} > {fmt.trim()} </Box>
                ))
                } 
            </Group>

          {fileName && !error && (
            <Group>
              <IconCode size={16}/>
              <Text>{fileName}</Text>
            </Group>
          )}

          {progress !== null && (
            <Progress value={progress} size="lg" radius="md" color="violet"/>
          )}

          {error && (
            <Group>
              <IconAlertTriangle size={16} color="red"/>
              <Text color="red">{error}</Text>
            </Group>
          )}
        </Stack>
      </Box>
    </Box>
  );
}
