/* ═══════════════════════════════════════════════════════════════════════
   PropagationPage — Full-screen propagation graph with controls
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo } from 'react';
import PropagationGraph from '../components/PropagationGraph';
import EnforcementModal from '../components/EnforcementModal';
import { generatePropagationData, generateEnforcementData } from '../hooks/useMockData';
import { RefreshCw, Maximize2, Filter } from 'lucide-react';

export default function PropagationPage() {
  const [enforcementData, setEnforcementData] = useState(null);
  const [graphKey, setGraphKey] = useState(0);
  const graphData = useMemo(() => generatePropagationData(), [graphKey]);

  const handleNodeClick = (node) => {
    if (node.type === 'url') {
      setEnforcementData(generateEnforcementData());
    }
  };

  const stats = useMemo(() => {
    const urlNodes = graphData.nodes.filter(n => n.type === 'url');
    const accountNodes = graphData.nodes.filter(n => n.type === 'account');
    const highRisk = urlNodes.filter(n => (n.morph_score || 0) > 70);
    return {
      totalNodes: graphData.nodes.length,
      accounts: accountNodes.length,
      urls: urlNodes.length,
      highRisk: highRisk.length,
      connections: graphData.links.length,
    };
  }, [graphData]);

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Propagation Network</h1>
          <p className="page-subtitle">
            Interactive visualization of viral content propagation chains
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <button className="btn btn-ghost" onClick={() => setGraphKey(k => k + 1)}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-ghost">
            <Filter size={14} /> Filter
          </button>
        </div>
      </div>

      {/* Graph stats bar */}
      <div style={{
        display: 'flex', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)',
        padding: 'var(--space-md) var(--space-lg)',
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)', fontSize: '0.8rem',
      }}>
        {[
          { label: 'Total Nodes', value: stats.totalNodes, color: 'var(--brand-primary-light)' },
          { label: 'Accounts', value: stats.accounts, color: '#FFFFFF' },
          { label: 'URLs Tracked', value: stats.urls, color: 'var(--brand-accent)' },
          { label: 'High Risk', value: stats.highRisk, color: 'var(--risk-critical)' },
          { label: 'Connections', value: stats.connections, color: 'var(--risk-warning)' },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>{item.label}:</span>
            <span style={{ fontWeight: 600, color: item.color }}>{item.value}</span>
          </div>
        ))}
      </div>

      <PropagationGraph
        nodes={graphData.nodes}
        links={graphData.links}
        onNodeClick={handleNodeClick}
        height={600}
      />

      <div style={{
        marginTop: 'var(--space-md)', fontSize: '0.75rem',
        color: 'var(--text-muted)', textAlign: 'center',
      }}>
        💡 Drag nodes to rearrange • Scroll to zoom • Click URL nodes to view enforcement details
      </div>

      {enforcementData && (
        <EnforcementModal
          data={enforcementData}
          onClose={() => setEnforcementData(null)}
          onAction={(action) => { console.log(action); setEnforcementData(null); }}
        />
      )}
    </div>
  );
}

