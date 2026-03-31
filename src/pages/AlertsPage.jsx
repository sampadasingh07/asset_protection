/* ═══════════════════════════════════════════════════════════════════════
   AlertsPage — Full alert history with filtering
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, AlertCircle, Info, Clock, Filter,
  CheckCircle, ExternalLink, Eye
} from 'lucide-react';

const SEVERITY_CONFIG = {
  CRITICAL: { icon: AlertTriangle, color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)' },
  WARNING: { icon: AlertCircle, color: 'var(--risk-warning)', bg: 'var(--risk-warning-bg)' },
  INFO: { icon: Info, color: 'var(--risk-info)', bg: 'var(--risk-info-bg)' },
};

function formatTime(isoString) {
  const d = new Date(isoString);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function AlertsPage({ alerts, onMarkRead, onMarkAllRead }) {
  const [filter, setFilter] = useState('ALL');

  const filtered = useMemo(() => {
    if (filter === 'ALL') return alerts;
    if (filter === 'UNREAD') return alerts.filter(a => !a.read);
    return alerts.filter(a => a.severity === filter);
  }, [alerts, filter]);

  const counts = useMemo(() => ({
    ALL: alerts.length,
    CRITICAL: alerts.filter(a => a.severity === 'CRITICAL').length,
    WARNING: alerts.filter(a => a.severity === 'WARNING').length,
    INFO: alerts.filter(a => a.severity === 'INFO').length,
    UNREAD: alerts.filter(a => !a.read).length,
  }), [alerts]);

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Alert Center</h1>
          <p className="page-subtitle">
            Real-time enforcement and detection alerts from all monitored platforms
          </p>
        </div>
        <button className="btn btn-ghost" onClick={onMarkAllRead}>
          <CheckCircle size={14} /> Mark all read
        </button>
      </div>

      {/* Filter tabs */}
      <div style={{
        display: 'flex', gap: 'var(--space-sm)',
        marginBottom: 'var(--space-xl)',
        flexWrap: 'wrap',
      }}>
        {['ALL', 'CRITICAL', 'WARNING', 'INFO', 'UNREAD'].map(f => (
          <button
            key={f}
            className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter(f)}
            style={filter === f ? {} : {
              color: f === 'CRITICAL' ? 'var(--risk-critical)' :
                     f === 'WARNING' ? 'var(--risk-warning)' :
                     f === 'INFO' ? 'var(--risk-info)' : undefined,
            }}
          >
            {f} ({counts[f]})
          </button>
        ))}
      </div>

      {/* Alerts list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        <AnimatePresence>
          {filtered.map((alert) => {
            const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.INFO;
            const Icon = config.icon;

            return (
              <motion.div
                key={alert.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                style={{
                  display: 'flex', gap: 'var(--space-md)',
                  padding: 'var(--space-lg)',
                  background: !alert.read ? 'rgba(255, 255, 255, 0.04)' : 'var(--bg-card)',
                  border: `1px solid ${!alert.read ? 'var(--border-default)' : 'var(--border-subtle)'}`,
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  borderLeft: `3px solid ${config.color}`,
                  transition: 'all 0.2s ease',
                }}
                onClick={() => onMarkRead(alert.id)}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-strong)'}
                onMouseLeave={e => { e.currentTarget.style.borderColor = !alert.read ? 'var(--border-default)' : 'var(--border-subtle)'; e.currentTarget.style.borderLeftColor = config.color; }}
              >
                {/* Severity icon */}
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-sm)',
                  background: config.bg, color: config.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <Icon size={18} />
                </div>

                {/* Content */}
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '0.875rem', color: 'var(--text-primary)',
                    fontWeight: !alert.read ? 500 : 400,
                    marginBottom: 4,
                  }}>
                    {alert.message}
                  </div>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 'var(--space-md)',
                    fontSize: '0.75rem', color: 'var(--text-muted)',
                    flexWrap: 'wrap',
                  }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Clock size={11} /> {formatTime(alert.timestamp)}
                    </span>
                    {alert.platform && (
                      <span className={`platform-badge ${alert.platform}`}>
                        {alert.platform}
                      </span>
                    )}
                    {alert.morphScore != null && (
                      <span style={{
                        fontWeight: 600, fontSize: '0.7rem',
                        color: alert.morphScore > 70 ? 'var(--risk-critical)' :
                               alert.morphScore > 40 ? 'var(--risk-warning)' : 'var(--risk-safe)',
                      }}>
                        Morph: {alert.morphScore}
                      </span>
                    )}
                    {alert.url && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 3, color: 'var(--brand-primary-light)' }}>
                        <ExternalLink size={10} />
                        <span style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {alert.url}
                        </span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Read indicator */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                  <span className={`risk-badge ${alert.severity === 'CRITICAL' ? 'critical' : alert.severity === 'WARNING' ? 'warning' : 'safe'}`}
                    style={{ fontSize: '0.65rem' }}
                  >
                    {alert.severity}
                  </span>
                  {!alert.read && (
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: 'var(--brand-primary)', marginTop: 4,
                      boxShadow: '0 0 8px rgba(255, 255, 255, 0.5)',
                    }} />
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {filtered.length === 0 && (
          <div style={{
            padding: 'var(--space-2xl)', textAlign: 'center',
            color: 'var(--text-muted)', fontSize: '0.9rem',
          }}>
            No alerts match this filter.
          </div>
        )}
      </div>
    </div>
  );
}

