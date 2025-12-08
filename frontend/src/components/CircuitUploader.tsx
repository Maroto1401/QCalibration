import React, { useCallback, useState } from 'react';
import { FileButton, Button, Text, Progress, Box, Group, ThemeIcon, Stack, Pill } from '@mantine/core';

import {
  IconUpload,
  IconCode,
  IconAlertTriangle,
  IconCircleCheck,
} from '@tabler/icons-react';

type Props = {
  onFile?: (file: File) => void;
  accept?: string;
};

export default function CircuitUploader({ onFile, accept = '.qasm,.qasm3,.json' }: Props) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [success, setSuccess] = useState(false);

  const validateAndHandleFile = useCallback(
    async (file?: File | null) => {
      setError(null);
      setFileName(null);
      setSuccess(false);
      if (!file) return;
      setFileName(file.name);

      let text: string;
      try {
        text = await file.text();
      } catch (e) {
        setError('Unable to read file');
        return;
      }

      const nameLower = (file.name || '').toLowerCase();
      const extMatch = nameLower.match(/\.([a-z0-9]+)$/);
      const ext = extMatch ? extMatch[1] : '';

      const detectByContent = (s: string) => {
        const first = s.trim().split(/\r?\n/).find((l) => l.trim().length > 0) || '';
        if (first.toUpperCase().includes('OPENQASM 3')) return 'qasm3';
        if (first.toUpperCase().includes('OPENQASM 2')) return 'qasm';
        if (s.trim().startsWith('{') || s.trim().startsWith('[')) return 'json';
        return null;
      };

      const contentType =
        ext === 'qasm3'
          ? 'qasm3'
          : ext === 'qasm'
          ? 'qasm'
          : ext === 'json'
          ? 'json'
          : detectByContent(text);

      const validateQasm = (s: string, expectedVersion?: 'qasm' | 'qasm3') => {
        const first = s.trim().split(/\r?\n/).find((l) => l.trim().length > 0) || '';
        if (!first.toUpperCase().includes('OPENQASM')) {
          return { valid: false, msg: 'Missing OPENQASM header' };
        }
        if (expectedVersion === 'qasm' && !first.includes('OPENQASM 2')) {
          return { valid: false, msg: 'Expected OpenQASM 2 header' };
        }
        if (expectedVersion === 'qasm3' && !first.includes('OPENQASM 3')) {
          return { valid: false, msg: 'Expected OpenQASM 3 header' };
        }
        return { valid: true, msg: '' };
      };

      const validateJson = (s: string) => {
        try {
          const obj = JSON.parse(s);
          if (obj && typeof obj === 'object') {
            if ('num_qubits' in obj || 'gates' in obj || 'qubits' in obj) {
              return { valid: true, msg:'Valid JSON'};
            }
            return { valid: false, msg: 'JSON does not look like a circuit (missing keys)' };
          }
          return { valid: false, msg: 'JSON root is not an object' };
        } catch (e) {
          return { valid: false, msg: 'Invalid JSON' };
        }
      };

      let validation = { valid: false, msg: 'Unknown file type' };

      if (contentType === 'qasm' || contentType === 'qasm3') {
        validation = validateQasm(text, contentType === 'qasm' ? 'qasm' : 'qasm3');
      } else if (contentType === 'json') {
        validation = validateJson(text);
      } else {
        validation = { valid: false, msg: 'Unrecognized file type. Provide .qasm, .qasm3 or .json' };
      }

      if (!validation.valid) {
        setError(validation.msg || 'Invalid circuit file');
        setProgress(null);
        return;
      }

      setProgress(10);
      const t1 = setTimeout(() => setProgress(60), 150);
      const t2 = setTimeout(() => setProgress(100), 400);
      const t3 = setTimeout(() => {
        setProgress(null);
        setSuccess(true);
      }, 700);

      if (onFile) {
        try {
          onFile(file);
        } catch (err: any) {
          setError(err?.message || 'Failed to process file');
          setSuccess(false);
        }
      }

      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(t3);
      };
    },
    [onFile]
  );

  const handleFileSelect = (file: File | null) => {
    if (file) void validateAndHandleFile(file);
  };

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      setError(null);
      const files = e.dataTransfer.files;
      if (!files || files.length === 0) return;
      void validateAndHandleFile(files[0]);
    },
    [validateAndHandleFile]
  );

  return (
    <Box style={{ maxWidth: 600, margin: '0 auto' }}>
      <Box
        onDrop={onDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragging(false);
        }}
        style={{
          border: `2px dashed ${
            dragging ? '#4c6ef5' : error ? '#fa5252' : success ? '#51cf66' : '#dee2e6'
          }`,
          borderRadius: 12,
          padding: 40,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: dragging
            ? '#edf2ff'
            : error
            ? '#fff5f5'
            : success
            ? '#ebfbee'
            : '#f8f9fa',
          transition: 'all 0.3s ease',
        }}
      >
        <Stack align="center">
          <ThemeIcon
            size={64}
            radius="xl"
            variant="light"
            color={dragging ? 'blue' : error ? 'red' : success ? 'green' : 'violet'}
          >
            {error ? (
              <IconAlertTriangle size={32} />
            ) : success ? (
              <IconCircleCheck size={32} />
            ) : (
              <IconUpload size={32} />
            )}
          </ThemeIcon>

          <div>
            <Text size="lg" style={{ marginBottom: 8, color: '#228be6' }}>
              Upload your Quantum Circuit
            </Text>
            <Text size="sm" color="dimmed">
              Drag and drop your circuit file here, or click to browse
            </Text>
          </div>

        <FileButton onChange={handleFileSelect} accept={accept}>
            {(props) => (
                <Button
                {...props}
                leftSection={<IconUpload size={16} />}
                variant="gradient"
                gradient={{ from: 'violet', to: 'blue', deg: 45 }}
                size="lg"
                radius="md"
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    cursor: 'pointer',
                    paddingLeft: 10,
                    paddingRight: 10,
                }}
                >
                Choose file
                </Button>
            )}
            </FileButton>

        <Group wrap='wrap' align="center">
            <Text size="xs">Supported formats:</Text>
            {accept.split(',').map((fmt) => (
                <Box
                key={fmt}
                style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
                }}
                >
                {fmt.trim()}
                </Box>
            ))}
            </Group>


          {fileName && !error && (
            <Box
              style={{
                background: success ? '#d3f9d8' : '#e7f5ff',
                border: `1px solid ${success ? '#8ce99a' : '#339af0'}`,
                borderRadius: 8,
                padding: '12px 16px',
                width: '100%',
                maxWidth: 400,
              }}
            >
              <Group>
                <IconCode size={16} color={success ? '#2b8a3e' : '#1971c2'} />
                <Text size="sm" style={{ color: success ? '#2b8a3e' : '#1971c2' }}>
                  {fileName}
                </Text>
              </Group>
            </Box>
          )}

          {progress !== null && (
            <Box style={{ width: '100%', maxWidth: 400 }}>
              <Progress value={progress} size="lg" radius="xl" striped color="violet" />
            </Box>
          )}

          {error && (
            <Box
              style={{
                background: '#ffe3e3',
                border: '1px solid #ffa8a8',
                borderRadius: 8,
                padding: '12px 16px',
                width: '100%',
                maxWidth: 400,
              }}
            >
              <Group>
                <IconAlertTriangle size={16} color="#c92a2a" />
                <Text size="sm" style={{ color: '#c92a2a' }}>
                  {error}
                </Text>
              </Group>
            </Box>
          )}
        </Stack>
      </Box>
    </Box>
  );
}
