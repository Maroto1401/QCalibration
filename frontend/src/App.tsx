import { useState } from 'react';
import { MantineProvider, Container, Title, Text } from '@mantine/core';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';

export default function App() {
  const [circuit, setCircuit] = useState<any>(null);

  return (
    <MantineProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage setCircuit={setCircuit} />} />
          <Route
            path="/circuit-analysis"
            element={<AnalysisPage circuit={circuit} />}
          />
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}
