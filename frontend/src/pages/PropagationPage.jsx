/* ═══════════════════════════════════════════════════════════════════════
   PropagationPage — Full-screen propagation graph with controls
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo, useEffect, useCallback } from 'react';
import PropagationGraph from '../components/PropagationGraph';
import EnforcementModal from '../components/EnforcementModal';
import {
  fetchAssets,
  fetchViolations,
  createEnforcementRecord,
  updateViolationStatus
} from '../lib/api';
import {
  buildAssetMap,
  buildPropagationGraph,
  mapViolationToEnforcementData,
} from '../lib/backendMappers';
import { RefreshCw, Filter } from 'lucide-react';

export default function PropagationPage() {
  const [enforcementData, setEnforcementData] = useState(null);
  const [assets, setAssets] = useState([]);
  const [violations, setViolations] = useState([]);
  const [showHighRiskOnly, setShowHighRiskOnly] = useState(false);
  const [actionStatus, setActionStatus] = useState(null);

  const assetMap = useMemo(() => buildAssetMap(assets), [assets]);
  const graphData = useMemo(() => {
    const base = buildPropagationGraph(violations, assetMap);
    if (!showHighRiskOnly) {
      return base;
    }

    const allowedNodeIds = new Set(
      base.nodes
        .filter((node) => node.type === 'url' && (node.morph_score || 0) >= 70)
        .map((node) => node.id)
    );

    base.links.forEach((link) => {
      if (allowedNodeIds.has(link.target)) {
        allowedNodeIds.add(link.source);
      }
    });

    return {
      nodes: base.nodes.filter((node) => allowedNodeIds.has(node.id)),
      links: base.links.filter((link) => allowedNodeIds.has(link.source) && allowedNodeIds.has(link.target)),
    };
  }, [violations, assetMap, showHighRiskOnly]);

  const loadData = useCallback(async () => {
    try {
      const [assetsPayload, violationsPayload] = await Promise.all([
        fetchAssets(),
        fetchViolations(),
      ]);
      setAssets(assetsPayload);
      setViolations(violationsPayload);
    } catch (error) {
      console.error('Failed to load propagation data:', error);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleNodeClick = (node) => {
    if (node.type === 'url' && node.violation_id) {
      const violation = violations.find((item) => item.id === node.violation_id);
      setEnforcementData(mapViolationToEnforcementData(violation, assetMap));
    }
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
          <button className="btn btn-ghost" onClick={loadData}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-ghost" onClick={() => setShowHighRiskOnly((prev) => !prev)}>
            <Filter size={14} /> {showHighRiskOnly ? 'Show All' : 'High-Risk Only'}
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

