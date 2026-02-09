import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SmartMeterMap from './pages/SmartMeterMap';
import GridTopology3D from './pages/GridTopology3D';
import VPPDashboard from './pages/VPPDashboard';
import ADRDashboard from './pages/ADRDashboard';
import ResilienceDashboard from './pages/ResilienceDashboard';

import { NetworkProvider } from './context/NetworkContext';

function App() {
  return (
    <NetworkProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/map" element={<SmartMeterMap />} />
          <Route path="/topology" element={<GridTopology3D />} />
          <Route path="/vpp" element={<VPPDashboard />} />
          <Route path="/adr" element={<ADRDashboard />} />
          <Route path="/resilience" element={<ResilienceDashboard />} />
        </Routes>
      </Router>
    </NetworkProvider>
  );
}

export default App;
