import { useState } from 'react';
import { MantineProvider } from '@mantine/core';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import '@mantine/core/styles.css';
import { CircuitMetadata } from './types';

export default function App() {
  const [circuitMetadata, setCircuitMetadata] = useState<CircuitMetadata | null>(null);
  
  return (
    <MantineProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={<HomePage setCircuitMetadata={setCircuitMetadata} />}
          />
          <Route
            path="/circuit-analysis"
            element={
              circuitMetadata ? (
                <AnalysisPage circuitMetadata={circuitMetadata} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}