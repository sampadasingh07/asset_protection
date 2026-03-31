/* ═══════════════════════════════════════════════════════════════════════
   Dashboard Page — Main overview with stats, graph, alerts, and morph score
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useMemo } from 'react';
import StatsCards from '../components/StatsCards';
import PropagationGraph from '../components/PropagationGraph';
import MorphScoreCard from '../components/MorphScoreCard';
import AlertPanel from '../components/AlertPanel';
import HighRiskTable from '../components/HighRiskTable';
import EnforcementModal from '../components/EnforcementModal';
import {
  generateDashboardStats, generatePropagationData, generateMorphScoreData,
  generateHighRiskAccounts, generateEnforcementData
} from '../hooks/useMockData';

export default function Dashboard({ alerts, onMarkRead, onMarkAllRead }) {
  const [enforcementData, setEnforcementData] = useState(null);

  // Generate mock data on mount (stable via useMemo)
  const stats = useMemo(() => generateDashboardStats(), []);
  const graphData = useMemo(() => generatePropagationData(), []);
  const morphData = useMemo(() => generateMorphScoreData(), []);
  const highRiskAccounts = useMemo(() => generateHighRiskAccounts(), []);

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

