/* ═══════════════════════════════════════════════════════════════════════
   HighRiskPage — Full high-risk account management page
   ═══════════════════════════════════════════════════════════════════════ */

import { useMemo, useState } from 'react';
import HighRiskTable from '../components/HighRiskTable';
import EnforcementModal from '../components/EnforcementModal';
import { generateHighRiskAccounts, generateEnforcementData } from '../hooks/useMockData';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function HighRiskPage() {
  const accounts = useMemo(() => generateHighRiskAccounts(), []);
  const [enforcementData, setEnforcementData] = useState(null);

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
        onEnforce={() => setEnforcementData(generateEnforcementData())}
      />

      {enforcementData && (
        <EnforcementModal
          data={enforcementData}
          onClose={() => setEnforcementData(null)}
          onAction={() => setEnforcementData(null)}
        />
      )}
    </div>
  );
}

