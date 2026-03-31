/* ═══════════════════════════════════════════════════════════════════════
   Sidebar — Navigation component
   ═══════════════════════════════════════════════════════════════════════ */

import {
  LayoutDashboard, Network, Shield, Bell, Upload, Activity,
  Users, FileSearch, Settings, HelpCircle, Zap
} from 'lucide-react';

const NAV_ITEMS = [
  { section: 'Overview' },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'propagation', label: 'Propagation Graph', icon: Network },
  { id: 'alerts', label: 'Alerts', icon: Bell, badge: null },
  { section: 'Management' },
  { id: 'assets', label: 'Protected Assets', icon: FileSearch },
  { id: 'high-risk', label: 'High-Risk Accounts', icon: Users },
  { id: 'enforcement', label: 'Enforcement', icon: Shield },
  { section: 'System' },
  { id: 'upload', label: 'Upload Asset', icon: Upload },
  { id: 'health', label: 'System Health', icon: Activity },
];

export default function Sidebar({ activePage, onNavigate, alertCount, connected }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Zap size={20} color="white" />
        </div>
        <div>
          <div className="sidebar-logo-text">DAP Shield</div>
          <div className="sidebar-logo-badge">AI-POWERED</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item, idx) => {
          if (item.section) {
            return (
              <div key={idx} className="sidebar-section-title">
                {item.section}
              </div>
            );
          }

          const Icon = item.icon;
          const isActive = activePage === item.id;
          const showBadge = item.id === 'alerts' && alertCount > 0;

          return (
            <div
              key={item.id}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={18} className="sidebar-link-icon" />
              <span>{item.label}</span>
              {showBadge && (
                <span className="sidebar-link-badge">{alertCount}</span>
              )}
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
          <span>{connected ? 'Live • Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </aside>
  );
}

