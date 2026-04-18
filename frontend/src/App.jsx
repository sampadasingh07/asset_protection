/* ═══════════════════════════════════════════════════════════════════════
   App.jsx — Main application shell
   Digital Asset Protection & Media Integrity Dashboard
   ═══════════════════════════════════════════════════════════════════════ */

import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { useAlerts } from './hooks/useAlerts';

// Pages
import Dashboard from './pages/Dashboard';
import PropagationPage from './pages/PropagationPage';
import AssetsPage from './pages/AssetsPage';
import AlertsPage from './pages/AlertsPage';
import HighRiskPage from './pages/HighRiskPage';
import EnforcementPage from './pages/EnforcementPage';
import UploadPage from './pages/UploadPage';
import SystemHealthPage from './pages/SystemHealthPage';

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const { alerts, connected, unreadCount, criticalCount, markRead, markAllRead } = useAlerts();

  const handleNavigate = (page) => {
    setActivePage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return (
          <Dashboard
            alerts={alerts}
            onMarkRead={markRead}
            onMarkAllRead={markAllRead}
          />
        );
      case 'propagation':
        return <PropagationPage />;
      case 'assets':
        return <AssetsPage />;
      case 'alerts':
        return (
          <AlertsPage
            alerts={alerts}
            onMarkRead={markRead}
            onMarkAllRead={markAllRead}
          />
        );
      case 'high-risk':
        return <HighRiskPage />;
      case 'enforcement':
        return <EnforcementPage />;
      case 'upload':
        return <UploadPage />;
      case 'health':
        return <SystemHealthPage />;
      default:
        return (
          <Dashboard
            alerts={alerts}
            onMarkRead={markRead}
            onMarkAllRead={markAllRead}
          />
        );
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        alertCount={unreadCount}
        connected={connected}
      />

      <Header
        unreadCount={unreadCount}
        criticalCount={criticalCount}
        onAlertClick={() => handleNavigate('alerts')}
        onNavigate={handleNavigate}
      />

      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;

