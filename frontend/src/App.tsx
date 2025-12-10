import { useState } from 'react';
import { MantineProvider} from '@mantine/core';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';

export default function App() {
  const [circuitId, setCircuitId] = useState<any>(null);

  return (
    <MantineProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage setCircuitId={setCircuitId} />} />
          <Route
            path="/circuit-analysis"
            element={<AnalysisPage circuitId={circuitId} />}
          />
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}
