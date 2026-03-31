/* ═══════════════════════════════════════════════════════════════════════
   EnforcementPage — Enforcement actions log
   ═══════════════════════════════════════════════════════════════════════ */

import { useMemo, useState } from 'react';
import EnforcementModal from '../components/EnforcementModal';
import { generateEnforcementData } from '../hooks/useMockData';
import { Gavel, CheckCircle, Clock, Eye, AlertTriangle, FileText } from 'lucide-react';

function generateEnforcementLog() {
  return Array.from({ length: 15 }, () => {
    const d = generateEnforcementData();
    const statuses = ['auto_takedown', 'human_review', 'pending', 'confirmed', 'rejected'];
    const s = statuses[Math.floor(Math.random() * statuses.length)];
    return { ...d, action_status: s };
  });
}

const STATUS_MAP = {
  auto_takedown: { label: 'Auto-Takedown', color: 'var(--risk-critical)', bg: 'var(--risk-critical-bg)', icon: Gavel },
  human_review: { label: 'Under Review', color: 'var(--risk-warning)', bg: 'var(--risk-warning-bg)', icon: Eye },
  pending: { label: 'Pending', color: 'var(--text-muted)', bg: 'var(--bg-surface)', icon: Clock },
  confirmed: { label: 'Confirmed', color: 'var(--risk-safe)', bg: 'var(--risk-safe-bg)', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'var(--text-muted)', bg: 'var(--bg-surface)', icon: AlertTriangle },
};

export default function EnforcementPage() {
  const log = useMemo(() => generateEnforcementLog(), []);
  const [selectedAction, setSelectedAction] = useState(null);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Enforcement Actions</h1>
        <p className="page-subtitle">
          DMCA takedowns, platform reports, and enforcement audit trail
        </p>
      </div>

      {/* Summary strip */}
      <div style={{
        display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)',
        flexWrap: 'wrap',
      }}>
        {Object.entries(STATUS_MAP).map(([key, cfg]) => {
          const count = log.filter(l => l.action_status === key).length;
          const Icon = cfg.icon;
          return (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '8px 16px', borderRadius: 'var(--radius-full)',
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
              fontSize: '0.8rem',
            }}>
              <Icon size={14} style={{ color: cfg.color }} />
              <span style={{ color: 'var(--text-secondary)' }}>{cfg.label}</span>
              <span style={{ fontWeight: 700, color: cfg.color }}>{count}</span>
            </div>
          );
        })}
      </div>

      {/* Enforcement log */}
      <div className="data-table-container">
        <div className="data-table-header">
          <div className="card-title">
            <FileText size={16} style={{ color: 'var(--brand-primary-light)' }} />
            Enforcement Audit Log
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Violation ID</th>
                <th>Asset</th>
                <th>Platform</th>
                <th>Account</th>
                <th>Morph Score</th>
                <th>Similarity</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {log.map((item, idx) => {
                const status = STATUS_MAP[item.action_status] || STATUS_MAP.pending;
                const StatusIcon = status.icon;
                return (
                  <tr key={idx}>
                    <td>
                      <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {item.violation_id?.slice(0, 8)}...
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-primary)', fontWeight: 500, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.asset_name}
                    </td>
                    <td>
                      <span className={`platform-badge ${item.platform}`}>{item.platform}</span>
                    </td>
                    <td style={{ color: 'var(--risk-critical)', fontSize: '0.8rem' }}>
                      {item.account_id}
                    </td>
                    <td>
                      <span style={{
                        fontWeight: 600,
                        color: item.morph_score > 70 ? 'var(--risk-critical)' :
                               item.morph_score > 40 ? 'var(--risk-warning)' : 'var(--risk-safe)',
                      }}>
                        {item.morph_score}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500 }}>
                      {(item.cosine_similarity * 100).toFixed(1)}%
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        fontSize: '0.7rem', fontWeight: 600,
                        padding: '3px 10px', borderRadius: 'var(--radius-full)',
                        background: status.bg, color: status.color,
                      }}>
                        <StatusIcon size={11} />
                        {status.label}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => setSelectedAction(item)}
                      >
                        <Eye size={13} /> View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selectedAction && (
        <EnforcementModal
          data={selectedAction}
          onClose={() => setSelectedAction(null)}
          onAction={() => setSelectedAction(null)}
        />
      )}
    </div>
  );
}

