/* ═══════════════════════════════════════════════════════════════════════
   Dashboard Page — Main overview with stats, graph, alerts, and morph score
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo, useEffect } from 'react';
import StatsCards from '../components/StatsCards';
import PropagationGraph from '../components/PropagationGraph';
import MorphScoreCard from '../components/MorphScoreCard';
import AlertPanel from '../components/AlertPanel';
import HighRiskTable from '../components/HighRiskTable';
import EnforcementModal from '../components/EnforcementModal';
import {
  fetchAssets,
  fetchViolations,
  fetchDashboardStats,
  createEnforcementRecord,
  updateViolationStatus
} from '../lib/api';
import {
  buildAssetMap,
  buildHighRiskAccounts,
  buildMorphScoreData,
  buildPropagationGraph,
  mapViolationToEnforcementData,
} from '../lib/backendMappers';

const DEFAULT_STATS = {
  totalAssets: 0,
  matchesDetected: 0,
  takedownsFiled: 0,
  highRiskAccounts: 0,
  changeAssets: 0,
  changeMatches: 0,
  changeTakedowns: 0,
  changeHighRisk: 0,
};

function mapDashboardStats(payload) {
  return {
    totalAssets: payload.asset_count ?? 0,
    matchesDetected: payload.violation_count ?? 0,
    takedownsFiled: payload.open_violations ?? 0,
    highRiskAccounts: payload.high_severity_violations ?? 0,
    changeAssets: 0,
    changeMatches: 0,
    changeTakedowns: 0,
    changeHighRisk: 0,
  };
}

export default function Dashboard({ alerts, onMarkRead, onMarkAllRead }) {
  const [enforcementData, setEnforcementData] = useState(null);
  const [stats, setStats] = useState(DEFAULT_STATS);
  const [assets, setAssets] = useState([]);
  const [violations, setViolations] = useState([]);
  const [actionStatus, setActionStatus] = useState(null);

  const assetMap = useMemo(() => buildAssetMap(assets), [assets]);
  const graphData = useMemo(() => buildPropagationGraph(violations, assetMap), [violations, assetMap]);
  const morphData = useMemo(() => buildMorphScoreData(violations), [violations]);
  const highRiskAccounts = useMemo(() => buildHighRiskAccounts(violations), [violations]);

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      try {
        const [statsPayload, assetsPayload, violationsPayload] = await Promise.all([
          fetchDashboardStats(),
          fetchAssets(),
          fetchViolations(),
        ]);
        if (isMounted) {
          setStats(mapDashboardStats(statsPayload));
          setAssets(assetsPayload);
          setViolations(violationsPayload);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleNodeClick = (node) => {
    if (node.type === 'url' && node.violation_id) {
      const violation = violations.find((item) => item.id === node.violation_id);
      const mapped = mapViolationToEnforcementData(violation, assetMap);
      setEnforcementData(mapped);
    }
  };

  const handleEnforce = (account) => {
    const violation = violations.find((item) => {
      const source = String(item.source_url || '').toLowerCase();
      return source.includes(String(account.account_id || '').replace('@', '').toLowerCase());
    }) || violations[0];
    setEnforcementData(mapViolationToEnforcementData(violation, assetMap));
  };

  const handleAction = async (action, data) => {
    setActionStatus(null);

    try {
      if (action === 'review') {
        // Update violation status to "under_review"
        await updateViolationStatus(data.violation_id, 'under_review');
        setActionStatus({ type: 'success', message: 'Violation marked for review' });
      } else if (action === 'takedown') {
        // Create enforcement record for DMCA takedown
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

      // Close modal after 2 seconds
      setTimeout(() => {
        setEnforcementData(null);
      }, 2000);
    } catch (error) {
      console.error(`Action failed: ${action}`, error);
      setActionStatus({ type: 'error', message: error.message || 'Action failed' });
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Command Center</h1>
        <p className="page-subtitle">
          Real-time overview of the Digital Asset Protection system
        </p>
      </div>

      <StatsCards stats={stats} />

      <div className="dashboard-grid">
        <PropagationGraph
          nodes={graphData.nodes}
          links={graphData.links}
          onNodeClick={handleNodeClick}
          height={460}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <MorphScoreCard {...morphData} />
          <AlertPanel
            alerts={alerts}
            onMarkRead={onMarkRead}
            onMarkAllRead={onMarkAllRead}
            maxItems={6}
          />
        </div>
      </div>

      <div style={{ marginTop: 'var(--space-lg)' }}>
        <HighRiskTable
          accounts={highRiskAccounts}
          onEnforce={handleEnforce}
        />
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

