/* ═══════════════════════════════════════════════════════════════════════
   MorphScoreCard — Radial gauge + sub-score rings + history sparkline
   Module 4C from GDG spec
   ═══════════════════════════════════════════════════════════════════════ */

import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';

function ScoreRing({ value, label, color, size = 56 }) {
  const radius = 15.9;
  const circumference = 2 * Math.PI * radius;
  const dashArray = `${(value / 100) * circumference} ${circumference}`;

  return (
    <div className="morph-subscore">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
          <circle cx="18" cy="18" r={radius} fill="none" stroke="rgba(255, 255, 255,0.1)" strokeWidth="3" />
          <circle
            cx="18" cy="18" r={radius} fill="none"
            stroke={color} strokeWidth="3"
            strokeDasharray={dashArray}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.8s ease' }}
          />
        </svg>
        <span style={{
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)'
        }}>
          {Math.round(value)}
        </span>
      </div>
      <span className="morph-subscore-label">{label}</span>
    </div>
  );
}

function getRiskLevel(score) {
  if (score > 70) return { label: 'HIGH RISK', color: '#FFFFFF', className: 'critical' };
  if (score > 40) return { label: 'MEDIUM', color: '#CCCCCC', className: 'warning' };
  return { label: 'LOW', color: '#888888', className: 'safe' };
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-default)',
      borderRadius: '8px',
      padding: '8px 12px',
      fontSize: '0.75rem',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
        Score: {payload[0].value}
      </div>
    </div>
  );
};

export default function MorphScoreCard({ currentScore, ganScore, freqScore, temporalScore, history }) {
  const risk = getRiskLevel(currentScore);
  const mainRadius = 50;
  const mainCircumference = 2 * Math.PI * mainRadius;
  const mainDashArray = `${(currentScore / 100) * mainCircumference} ${mainCircumference}`;

  return (
    <div className="morph-card">
      <div className="card-header">
        <div className="card-title">
          <span style={{ fontSize: '1.1rem' }}>🔬</span>
          Morph Score Analysis
        </div>
        <span className={`risk-badge ${risk.className}`}>
          {risk.label}
        </span>
      </div>

      <div className="morph-main-score">
        {/* Main radial gauge */}
        <div className="morph-ring-container" style={{ width: 110, height: 110 }}>
          <svg viewBox="0 0 120 120" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
            <circle cx="60" cy="60" r={mainRadius} fill="none" stroke="rgba(255, 255, 255,0.08)" strokeWidth="10" />
            <circle
              cx="60" cy="60" r={mainRadius} fill="none"
              stroke={risk.color} strokeWidth="10"
              strokeDasharray={mainDashArray}
              strokeLinecap="round"
              style={{ transition: 'stroke-dasharray 1s ease' }}
            />
          </svg>
          <div className="morph-ring-label">
            <span className="morph-ring-value" style={{ color: risk.color }}>
              {Math.round(currentScore)}
            </span>
            <span className="morph-ring-unit">/ 100</span>
          </div>
        </div>

        {/* Sub-scores */}
        <div className="morph-subscores">
          <ScoreRing value={ganScore} label="GAN" color="#FFFFFF" />
          <ScoreRing value={freqScore} label="DCT" color="#CCCCCC" />
          <ScoreRing value={temporalScore} label="Temporal" color="#888888" />
        </div>
      </div>

      {/* Score formula */}
      <div style={{
        fontSize: '0.7rem', color: 'var(--text-muted)',
        padding: '8px 12px', background: 'var(--bg-card)',
        borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-md)',
        fontFamily: 'monospace', letterSpacing: '0.03em',
        border: '1px solid var(--border-subtle)',
      }}>
        MorphScore = 0.40 × GAN + 0.35 × DCT + 0.25 × Temporal
      </div>

      {/* History sparkline */}
      <div style={{ height: 90 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 5, right: 5, bottom: 0, left: 5 }}>
            <defs>
              <linearGradient id="morphGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={risk.color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={risk.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255,0.06)" />
            <XAxis dataKey="time" hide />
            <YAxis domain={[0, 100]} hide />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="score"
              stroke={risk.color} strokeWidth={2}
              fill="url(#morphGrad)"
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

