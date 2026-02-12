// Main React app - router and layout configuration
import { useState } from 'react';
import { MantineProvider } from '@mantine/core';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import '@mantine/core/styles.css';
import { CircuitMetadata } from './types';
import TopologyPage from './pages/TopologyPage';
import TopologyView from './components/topologyComponents/TopologyView';
import TranspilationSelectorPage from './pages/TranspilationSelectorPage';

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
          <Route path="/topology" element={<TopologyPage />} />
          <Route path="/topology/preview" element={<TopologyView />} />
          <Route path="/transpilation-selector" element={<TranspilationSelectorPage />} />

        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}