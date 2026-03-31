/* ═══════════════════════════════════════════════════════════════════════
   StatsCards — Dashboard summary statistics
   ═══════════════════════════════════════════════════════════════════════ */

import { Shield, Search, Gavel, UserX, TrendingUp, TrendingDown } from 'lucide-react';

const CARD_CONFIG = [
  {
    key: 'totalAssets',
    label: 'Protected Assets',
    icon: Shield,
    color: '#FFFFFF',
    bg: 'rgba(255, 255, 255, 0.1)',
    changeKey: 'changeAssets',
  },
  {
    key: 'matchesDetected',
    label: 'Matches Detected',
    icon: Search,
    color: '#F5F5F5',
    bg: 'rgba(255, 255, 255, 0.1)',
    changeKey: 'changeMatches',
  },
  {
    key: 'takedownsFiled',
    label: 'Takedowns Filed',
    icon: Gavel,
    color: '#FFFFFF',
    bg: 'rgba(255, 255, 255, 0.1)',
    changeKey: 'changeTakedowns',
  },
  {
    key: 'highRiskAccounts',
    label: 'High-Risk Accounts',
    icon: UserX,
    color: '#CCCCCC',
    bg: 'rgba(255, 255, 255, 0.1)',
    changeKey: 'changeHighRisk',
  },
];

export default function StatsCards({ stats }) {
  return (
    <div className="stats-grid">
      {CARD_CONFIG.map((cfg, idx) => {
        const Icon = cfg.icon;
        const value = stats[cfg.key];
        const change = stats[cfg.changeKey];
        const isPositive = change >= 0;

        return (
          <div
            key={cfg.key}
            className="stat-card animate-slide-up"
            style={{
              '--stat-color': cfg.color,
              '--stat-bg': cfg.bg,
              animationDelay: `${idx * 80}ms`,
            }}
          >
            <div className="stat-icon" style={{ background: cfg.bg, color: cfg.color }}>
              <Icon size={20} />
            </div>
            <div className="stat-value">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
            <div className="stat-label">{cfg.label}</div>
            <div className={`stat-change ${isPositive ? 'up' : 'down'}`}>
              {isPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
              {isPositive ? '+' : ''}{change}% this week
            </div>
          </div>
        );
      })}
    </div>
  );
}

