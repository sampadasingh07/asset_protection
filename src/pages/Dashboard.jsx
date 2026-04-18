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
import { fetchDashboardStats } from '../lib/api';
import {
  generatePropagationData, generateMorphScoreData,
  generateHighRiskAccounts, generateEnforcementData
} from '../hooks/useMockData';

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

  const graphData = useMemo(() => generatePropagationData(), []);
  const morphData = useMemo(() => generateMorphScoreData(), []);
  const highRiskAccounts = useMemo(() => generateHighRiskAccounts(), []);

  useEffect(() => {
    let isMounted = true;

    const loadStats = async () => {
      try {
        const payload = await fetchDashboardStats();
        if (isMounted) {
          setStats(mapDashboardStats(payload));
        }
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      }
    };

    loadStats();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleNodeClick = (node) => {
    if (node.type === 'url') {
      setEnforcementData(generateEnforcementData());
    }
  };

  const handleEnforce = () => {
    setEnforcementData(generateEnforcementData());
  };

  const handleAction = (action, data) => {
    console.log(`Action: ${action}`, data);
    setEnforcementData(null);
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
    </div>
  );
}

