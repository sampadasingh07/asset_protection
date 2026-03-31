/* ═══════════════════════════════════════════════════════════════════════
   SystemHealthPage — System metrics and monitoring
   ═══════════════════════════════════════════════════════════════════════ */

import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, LineChart, Line
} from 'recharts';
import {
  Activity, Cpu, Database, HardDrive, Wifi, Zap,
  Server, CheckCircle, AlertCircle
} from 'lucide-react';

function genTimeSeries(points = 30, base = 50, variance = 20) {
  return Array.from({ length: points }, (_, i) => ({
    time: `${30 - i}m`,
    value: Math.round(base + (Math.random() - 0.5) * variance * 2),
  }));
}

const SERVICES = [
  { name: 'FastAPI Gateway', status: 'healthy', latency: '12ms', uptime: '99.97%', icon: Server, port: 8000 },
  { name: 'Milvus Vector DB', status: 'healthy', latency: '18ms', uptime: '99.95%', icon: Database, port: 19530 },
  { name: 'PostgreSQL 16', status: 'healthy', latency: '4ms', uptime: '99.99%', icon: HardDrive, port: 5432 },
  { name: 'Neo4j Graph DB', status: 'healthy', latency: '22ms', uptime: '99.91%', icon: Database, port: 7687 },
  { name: 'Redis Queue', status: 'healthy', latency: '1ms', uptime: '99.99%', icon: Zap, port: 6379 },
  { name: 'Celery Workers', status: 'warning', latency: '—', uptime: '99.82%', icon: Cpu, port: null },
  { name: 'Playwright Crawlers', status: 'healthy', latency: '—', uptime: '99.88%', icon: Wifi, port: null },
  { name: 'WebSocket Hub', status: 'healthy', latency: '3ms', uptime: '99.96%', icon: Activity, port: 8000 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
      borderRadius: '8px', padding: '8px 12px', fontSize: '0.75rem',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{ color: 'var(--text-muted)' }}>{label}</div>
      <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{payload[0].value}%</div>
    </div>
  );
};

export default function SystemHealthPage() {
  const cpuData = useMemo(() => genTimeSeries(30, 35, 15), []);
  const memData = useMemo(() => genTimeSeries(30, 62, 10), []);
  const queueData = useMemo(() => genTimeSeries(30, 150, 80).map(d => ({ ...d, value: Math.abs(d.value) })), []);
  const latencyData = useMemo(() => genTimeSeries(30, 15, 8).map(d => ({ ...d, value: Math.abs(d.value) })), []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">System Health</h1>
        <p className="page-subtitle">
          Infrastructure monitoring — Kubernetes cluster, databases, and worker pools
        </p>
      </div>

      {/* Service Status Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: 'var(--space-md)', marginBottom: 'var(--space-xl)',
      }}>
        {SERVICES.map((svc, idx) => {
          const Icon = svc.icon;
          const isHealthy = svc.status === 'healthy';
          return (
            <div key={idx} className="card animate-slide-up" style={{ animationDelay: `${idx * 50}ms` }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 'var(--radius-sm)',
                    background: isHealthy ? 'var(--risk-safe-bg)' : 'var(--risk-warning-bg)',
                    color: isHealthy ? 'var(--risk-safe)' : 'var(--risk-warning)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                      {svc.name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {svc.port ? `Port ${svc.port}` : 'Distributed'}
                    </div>
                  </div>
                </div>
                {isHealthy
                  ? <CheckCircle size={16} style={{ color: 'var(--risk-safe)' }} />
                  : <AlertCircle size={16} style={{ color: 'var(--risk-warning)' }} />
                }
              </div>
              <div style={{
                display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-md)',
                paddingTop: 'var(--space-sm)', borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
              }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Latency: </span>
                  <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{svc.latency}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Uptime: </span>
                  <span style={{ fontWeight: 600, color: 'var(--risk-safe)' }}>{svc.uptime}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Metric Charts */}
      <div className="dashboard-grid-full">
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Cpu size={15} /> CPU Usage</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--risk-safe)', fontWeight: 600 }}>
              {cpuData[cpuData.length - 1]?.value}%
            </span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cpuData}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FFFFFF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#FFFFFF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255,0.06)" />
                <XAxis dataKey="time" tick={{ fill: '#888888', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#888888', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="value" stroke="#FFFFFF" strokeWidth={2} fill="url(#cpuGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title"><HardDrive size={15} /> Memory Usage</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--risk-warning)', fontWeight: 600 }}>
              {memData[memData.length - 1]?.value}%
            </span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={memData}>
                <defs>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F5F5F5" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F5F5F5" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255,0.06)" />
                <XAxis dataKey="time" tick={{ fill: '#888888', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#888888', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="value" stroke="#F5F5F5" strokeWidth={2} fill="url(#memGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title"><Zap size={15} /> Queue Depth</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--brand-primary-light)', fontWeight: 600 }}>
              {queueData[queueData.length - 1]?.value} tasks
            </span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={queueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255,0.06)" />
                <XAxis dataKey="time" tick={{ fill: '#888888', fontSize: 10 }} />
                <YAxis tick={{ fill: '#888888', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="value" stroke="#E0E0E0" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title"><Activity size={15} /> API Latency (p95)</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--risk-safe)', fontWeight: 600 }}>
              {latencyData[latencyData.length - 1]?.value}ms
            </span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255,0.06)" />
                <XAxis dataKey="time" tick={{ fill: '#888888', fontSize: 10 }} />
                <YAxis tick={{ fill: '#888888', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="value" stroke="#888888" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

