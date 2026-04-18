/* ═══════════════════════════════════════════════════════════════════════
   AlertPanel — Real-time alert notification feed
   Module 4B from GDG spec
   ═══════════════════════════════════════════════════════════════════════ */

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, AlertCircle, Info, Clock, ExternalLink } from 'lucide-react';

const SEVERITY_CONFIG = {
  CRITICAL: {
    icon: AlertTriangle,
    className: 'critical',
    emoji: '🚨',
  },
  WARNING: {
    icon: AlertCircle,
    className: 'warning',
    emoji: '⚠️',
  },
  INFO: {
    icon: Info,
    className: 'info',
    emoji: 'ℹ️',
  },
};

function formatTimeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function AlertPanel({ alerts, onMarkRead, onMarkAllRead, maxItems = 20 }) {
  const visibleAlerts = alerts.slice(0, maxItems);
  const unreadCount = alerts.filter(a => !a.read).length;

  return (
    <div className="alert-panel">
      <div className="alert-panel-header">
        <div className="card-title">
          <span style={{ fontSize: '1rem' }}>🔔</span>
          Live Alerts
          {unreadCount > 0 && (
            <span style={{
              fontSize: '0.65rem', fontWeight: 700,
              background: 'var(--risk-critical)',
              color: 'white', padding: '1px 8px',
              borderRadius: 'var(--radius-full)',
              marginLeft: '4px',
            }}>
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button className="mark-all-btn" onClick={onMarkAllRead}>
            Mark all read
          </button>
        )}
      </div>

      <div className="alert-panel-body">
        <AnimatePresence initial={false}>
          {visibleAlerts.map((alert) => {
            const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.INFO;
            const Icon = config.icon;

            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: 30, height: 0 }}
                animate={{ opacity: 1, x: 0, height: 'auto' }}
                exit={{ opacity: 0, x: -20, height: 0 }}
                transition={{ duration: 0.35, ease: 'easeOut' }}
                className={`alert-item ${config.className} ${!alert.read ? 'unread' : ''}`}
                onClick={() => onMarkRead(alert.id)}
              >
                <div className={`alert-severity-icon ${config.className}`}>
                  <Icon size={15} />
                </div>
                <div className="alert-content">
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-meta">
                    <Clock size={10} />
                    <span>{formatTimeAgo(alert.timestamp)}</span>
                    {alert.platform && (
                      <span className="alert-platform-tag">{alert.platform}</span>
                    )}
                    {alert.morphScore && (
                      <span style={{
                        fontSize: '0.65rem', fontWeight: 600,
                        color: alert.morphScore > 70 ? 'var(--risk-critical)' :
                               alert.morphScore > 40 ? 'var(--risk-warning)' : 'var(--risk-safe)',
                      }}>
                        MS: {alert.morphScore}
                      </span>
                    )}
                  </div>
                </div>
                {alert.url && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(alert.url, '_blank');
                    }}
                    title="Open external URL"
                  >
                    <ExternalLink size={13} />
                  </button>
                )}
                {!alert.read && (
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--brand-primary-light)',
                    flexShrink: 0, alignSelf: 'flex-start', marginTop: 8,
                  }} />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {visibleAlerts.length === 0 && (
          <div style={{
            padding: 'var(--space-2xl)',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}>
            No alerts yet. System is monitoring...
          </div>
        )}
      </div>
    </div>
  );
}

