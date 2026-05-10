import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnalysisProvider } from './state/analysisContext';
import AppShell from './components/layout/AppShell';
import DashboardPage from './pages/DashboardPage';
import AboutPage from './pages/AboutPage';

function App() {
  return (
    <AnalysisProvider>
      <Router>
        <AppShell>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </AppShell>
      </Router>
    </AnalysisProvider>
  );
}

export default App;
