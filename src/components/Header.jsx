/* ═══════════════════════════════════════════════════════════════════════
   Header — Top bar with search, alerts, and user avatar
   ═══════════════════════════════════════════════════════════════════════ */

import { Search, Bell, Settings, Moon } from 'lucide-react';

export default function Header({ unreadCount, criticalCount, onAlertClick }) {
  return (
    <header className="header">
      <div className="header-left">
        <div className="header-search">
          <Search size={15} style={{ opacity: 0.4, flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search assets, accounts, URLs..."
            id="global-search"
          />
          <kbd style={{
            fontSize: '0.6rem',
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            whiteSpace: 'nowrap'
          }}>⌘ K</kbd>
        </div>
      </div>

      <div className="header-right">
        <button className="header-btn" title="Toggle theme">
          <Moon size={16} />
        </button>

        <button className="header-btn" title="Settings">
          <Settings size={16} />
        </button>

        <button
          className="header-btn"
          onClick={onAlertClick}
          title={`${unreadCount} unread alerts`}
          id="alert-bell-btn"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="header-btn-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        <div className="header-avatar" title="Admin User">
          AD
        </div>
      </div>
    </header>
  );
}

