/* ═══════════════════════════════════════════════════════════════════════
   HighRiskTable — Sortable account table with drill-down
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Eye, Shield, ExternalLink, AlertTriangle } from 'lucide-react';

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function HighRiskTable({ accounts, onViewAccount, onEnforce }) {
  const [sortKey, setSortKey] = useState('risk_score');
  const [sortDir, setSortDir] = useState('desc');
  const [expandedRow, setExpandedRow] = useState(null);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = useMemo(() => {
    return [...accounts].sort((a, b) => {
      let aVal = a[sortKey];
      let bVal = b[sortKey];
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [accounts, sortKey, sortDir]);

  const SortIcon = ({ column }) => {
    if (sortKey !== column) return <span className="sort-icon">⇅</span>;
    return sortDir === 'asc'
      ? <ChevronUp size={12} style={{ color: 'var(--brand-primary-light)' }} />
      : <ChevronDown size={12} style={{ color: 'var(--brand-primary-light)' }} />;
  };

  const getRiskColor = (score) => {
    if (score > 75) return 'var(--risk-critical)';
    if (score > 45) return 'var(--risk-warning)';
    return 'var(--risk-safe)';
  };

  return (
    <div className="data-table-container">
      <div className="data-table-header">
        <div className="card-title">
          <AlertTriangle size={16} style={{ color: 'var(--risk-warning)' }} />
          High-Risk Accounts
          <span style={{
            fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)',
            background: 'var(--bg-surface)', padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
          }}>
            {accounts.length} tracked
          </span>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('account_id')} className={sortKey === 'account_id' ? 'sorted' : ''}>
                Account <SortIcon column="account_id" />
              </th>
              <th onClick={() => handleSort('platform')} className={sortKey === 'platform' ? 'sorted' : ''}>
                Platform <SortIcon column="platform" />
              </th>
              <th onClick={() => handleSort('risk_score')} className={sortKey === 'risk_score' ? 'sorted' : ''}>
                Risk Score <SortIcon column="risk_score" />
              </th>
              <th onClick={() => handleSort('violation_count')} className={sortKey === 'violation_count' ? 'sorted' : ''}>
                Violations <SortIcon column="violation_count" />
              </th>
              <th onClick={() => handleSort('total_morph_score_avg')} className={sortKey === 'total_morph_score_avg' ? 'sorted' : ''}>
                Avg Morph <SortIcon column="total_morph_score_avg" />
              </th>
              <th>Status</th>
              <th onClick={() => handleSort('last_seen')} className={sortKey === 'last_seen' ? 'sorted' : ''}>
                Last Seen <SortIcon column="last_seen" />
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((account) => (
              <>
                <tr key={account.id} onClick={() => setExpandedRow(expandedRow === account.id ? null : account.id)}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '6px',
                        background: `linear-gradient(135deg, ${getRiskColor(account.risk_score)}, transparent)`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.7rem', fontWeight: 700, color: 'white',
                        opacity: 0.9,
                      }}>
                        {account.account_id.slice(1, 3).toUpperCase()}
                      </div>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                        {account.account_id}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`platform-badge ${account.platform}`}>
                      {account.platform}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: 50, height: 5, borderRadius: '3px',
                        background: 'var(--bg-surface)', overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${account.risk_score}%`, height: '100%',
                          background: getRiskColor(account.risk_score),
                          borderRadius: '3px',
                          transition: 'width 0.5s ease',
                        }} />
                      </div>
                      <span style={{ fontWeight: 600, color: getRiskColor(account.risk_score), fontSize: '0.85rem' }}>
                        {account.risk_score}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 600,
                      color: account.violation_count > 10 ? 'var(--risk-critical)' :
                             account.violation_count > 5 ? 'var(--risk-warning)' : 'var(--text-primary)',
                    }}>
                      {account.violation_count}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 500,
                      color: account.total_morph_score_avg > 60 ? 'var(--risk-critical)' :
                             account.total_morph_score_avg > 35 ? 'var(--risk-warning)' : 'var(--text-secondary)',
                    }}>
                      {account.total_morph_score_avg}
                    </span>
                  </td>
                  <td>
                    {account.is_watchlisted ? (
                      <span className="risk-badge critical" style={{ fontSize: '0.65rem' }}>
                        <Eye size={10} /> WATCHLISTED
                      </span>
                    ) : (
                      <span className="risk-badge safe" style={{ fontSize: '0.65rem' }}>
                        MONITORED
                      </span>
                    )}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {formatDate(account.last_seen)}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); onViewAccount?.(account); }}
                        title="View details"
                      >
                        <Eye size={13} />
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={(e) => { e.stopPropagation(); onEnforce?.(account); }}
                        title="Enforce"
                      >
                        <Shield size={13} />
                      </button>
                    </div>
                  </td>
                </tr>

                {/* Expanded row details */}
                {expandedRow === account.id && (
                  <tr key={`${account.id}-detail`}>
                    <td colSpan={8} style={{ padding: 0 }}>
                      <div style={{
                        background: 'var(--bg-elevated)',
                        padding: 'var(--space-lg)',
                        margin: '0 var(--space-md) var(--space-sm)',
                        borderRadius: 'var(--radius-sm)',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: 'var(--space-md)',
                        fontSize: '0.8rem',
                        animation: 'slideUp 0.3s ease',
                      }}>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: 4 }}>First Seen</div>
                          <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{formatDate(account.first_seen)}</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: 4 }}>Assets Targeted</div>
                          <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{account.assets_targeted}</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: 4 }}>Avg Morph Score</div>
                          <div style={{ color: getRiskColor(account.total_morph_score_avg), fontWeight: 600 }}>
                            {account.total_morph_score_avg}/100
                          </div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: 4 }}>Threat Level</div>
                          <span className={`risk-badge ${account.risk_score > 75 ? 'critical' : account.risk_score > 45 ? 'warning' : 'safe'}`}>
                            {account.risk_score > 75 ? 'SEVERE' : account.risk_score > 45 ? 'ELEVATED' : 'LOW'}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

