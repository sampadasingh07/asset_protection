/* ═══════════════════════════════════════════════════════════════════════
   HighRiskPage — Full high-risk account management page
   ═══════════════════════════════════════════════════════════════════════ */

import { useMemo, useState, useEffect, useCallback } from 'react';
import HighRiskTable from '../components/HighRiskTable';
import EnforcementModal from '../components/EnforcementModal';
import {
  fetchAssets,
  fetchViolations,
  createEnforcementRecord,
  updateViolationStatus
} from '../lib/api';
import {
  buildAssetMap,
  buildHighRiskAccounts,
  mapViolationToEnforcementData,
} from '../lib/backendMappers';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function HighRiskPage() {
  const [assets, setAssets] = useState([]);
  const [violations, setViolations] = useState([]);
  const [enforcementData, setEnforcementData] = useState(null);
  const [actionStatus, setActionStatus] = useState(null);

  const assetMap = useMemo(() => buildAssetMap(assets), [assets]);
  const accounts = useMemo(() => buildHighRiskAccounts(violations), [violations]);

  const loadData = useCallback(async () => {
    try {
      const [assetsPayload, violationsPayload] = await Promise.all([
        fetchAssets(),
        fetchViolations(),
      ]);
      setAssets(assetsPayload);
      setViolations(violationsPayload);
    } catch (error) {
      console.error('Failed to load high-risk accounts:', error);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const platformDistribution = useMemo(() => {
    const dist = {};
    accounts.forEach(a => { dist[a.platform] = (dist[a.platform] || 0) + 1; });
    return Object.entries(dist).map(([name, value]) => ({ name, value }));
  }, [accounts]);

  const riskDistribution = useMemo(() => {
    return [
      { range: '0-25', count: accounts.filter(a => a.risk_score <= 25).length, color: '#888888' },
      { range: '26-50', count: accounts.filter(a => a.risk_score > 25 && a.risk_score <= 50).length, color: '#F5F5F5' },
      { range: '51-75', count: accounts.filter(a => a.risk_score > 50 && a.risk_score <= 75).length, color: '#CCCCCC' },
      { range: '76-100', count: accounts.filter(a => a.risk_score > 75).length, color: '#FFFFFF' },
    ];
  }, [accounts]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
        borderRadius: '8px', padding: '8px 12px', fontSize: '0.75rem',
        boxShadow: 'var(--shadow-md)',
      }}>
        <div style={{ color: 'var(--text-muted)' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{payload[0].value} accounts</div>
      </div>
    );
  };

  const handleAction = async (action, data) => {
    setActionStatus(null);

    try {
      if (action === 'review') {
        await updateViolationStatus(data.violation_id, 'under_review');
        setActionStatus({ type: 'success', message: 'Violation marked for review' });
      } else if (action === 'takedown') {
        await createEnforcementRecord(
          data.violation_id,
          'DMCA_TAKEDOWN',
          data.platform,
          {
            notes: `Auto-generated DMCA takedown for high-risk content (score: ${data.morph_score})`,
            status: 'PENDING'
          }
        );
        await updateViolationStatus(data.violation_id, 'enforcement_initiated');
        setActionStatus({ type: 'success', message: 'DMCA takedown filed successfully' });
      }

      setTimeout(() => {
        setEnforcementData(null);
      }, 2000);
    } catch (error) {
      console.error(`Action failed: ${action}`, error);
      setActionStatus({ type: 'error', message: error.message || 'Action failed' });
    }
  };

  const handleEnforceAccount = (account) => {
    const violation = violations.find((item) => item.id === account.sample_violation_id)
      || violations.find((item) => String(item.source_url || '').includes(account.account_id.replace('@', '')))
      || violations[0];
    setEnforcementData(mapViolationToEnforcementData(violation, assetMap));
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">High-Risk Accounts</h1>
        <p className="page-subtitle">
          Track repeat offenders and serial infringers across all platforms
        </p>
      </div>

      {/* Distribution Charts */}
      <div className="dashboard-grid-full" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Risk Score Distribution</div>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistribution} barSize={40}>
                <XAxis dataKey="range" tick={{ fill: '#9595C4', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9595C4', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {riskDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Platform Distribution</div>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={platformDistribution} barSize={40} layout="vertical">
                <XAxis type="number" tick={{ fill: '#9595C4', fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={70} tick={{ fill: '#9595C4', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" fill="#FFFFFF" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <HighRiskTable
        accounts={accounts}
        onEnforce={handleEnforceAccount}
      />

      {enforcementData && (
        <EnforcementModal
          data={enforcementData}
          onClose={() => setEnforcementData(null)}
          onAction={handleAction}
        />
      )}

      {actionStatus && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '16px 20px',
            borderRadius: '8px',
            background: actionStatus.type === 'success' ? 'var(--risk-safe)' : 'var(--risk-critical)',
            color: 'white',
            zIndex: 1000,
            fontWeight: '500',
          }}
        >
          {actionStatus.message}
        </div>
      )}
    </div>
  );
}

