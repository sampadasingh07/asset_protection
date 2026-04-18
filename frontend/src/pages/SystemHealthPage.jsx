/* ═══════════════════════════════════════════════════════════════════════
   SystemHealthPage — System metrics and monitoring
   ═══════════════════════════════════════════════════════════════════════ */

import { useEffect, useMemo, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, LineChart, Line,
} from 'recharts';
import {
  Activity, Cpu, Database, HardDrive, Wifi, Zap,
  Server, CheckCircle, AlertCircle,
} from 'lucide-react';
import { fetchHealthStatus, fetchSystemStats } from '../lib/api';

function pushSample(history, value, maxPoints = 30) {
  const sample = {
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: Math.round(Math.max(0, Number(value) || 0)),
  };
  return [...history, sample].slice(-maxPoints);
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
      borderRadius: '8px', padding: '8px 12px', fontSize: '0.75rem',
      boxShadow: 'var(--shadow-md)',
    }}>
      <div style={{ color: 'var(--text-muted)' }}>{label}</div>
      <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{payload[0].value}</div>
    </div>
  );
};

export default function SystemHealthPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);
  const [systemStats, setSystemStats] = useState({
    cpu_percent: 0,
    memory_percent: 0,
    disk_percent: 0,
    process_uptime_seconds: 0,
    request_latency_p95_ms: 0,
    requests_last_minute: 0,
    queue_depth: 0,
    queued_assets: 0,
    processing_assets: 0,
    ready_assets: 0,
    open_violations: 0,
    high_severity_violations: 0,
    task_mode: 'inline',
    ai_mode: 'fallback',
  });

  const [cpuData, setCpuData] = useState([]);
  const [memData, setMemData] = useState([]);
  const [queueData, setQueueData] = useState([]);
  const [latencyData, setLatencyData] = useState([]);

  useEffect(() => {
    let alive = true;
    let pollTimer = null;

    const pollSystemStats = async () => {
      const snapshot = await fetchSystemStats();
      if (!alive) return;

      setSystemStats(snapshot);
      setCpuData((prev) => pushSample(prev, snapshot.cpu_percent));
      setMemData((prev) => pushSample(prev, snapshot.memory_percent));
      setQueueData((prev) => pushSample(prev, snapshot.queue_depth));
      setLatencyData((prev) => pushSample(prev, snapshot.request_latency_p95_ms));
    };

    const load = async () => {
      setError('');
      setLoading(true);
      try {
        const healthPayload = await fetchHealthStatus();
        if (!alive) return;
        setHealth(healthPayload);

        await pollSystemStats();
        pollTimer = setInterval(() => {
          pollSystemStats().catch((pollError) => {
            if (alive) {
              console.error('Failed to refresh system stats:', pollError);
            }
          });
        }, 5000);
      } catch (fetchError) {
        if (alive) {
          setError(fetchError instanceof Error ? fetchError.message : 'Failed to load system health.');
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      alive = false;
      if (pollTimer) {
        clearInterval(pollTimer);
      }
    };
  }, []);

  const services = useMemo(() => {
    const backendHealthy = health?.status === 'ok';
    const aiAvailable = String(systemStats.ai_mode || health?.ai_mode || 'fallback') === 'full';
    const taskMode = String(systemStats.task_mode || health?.task_mode || 'inline');

    return [
      {
        name: 'FastAPI API',
        status: backendHealthy ? 'healthy' : 'warning',
        latency: backendHealthy ? `${Math.round(systemStats.request_latency_p95_ms)}ms p95` : 'offline',
        uptime: backendHealthy ? 'up' : 'degraded',
        icon: Server,
        port: 8000,
      },
      {
        name: 'AI Engine',
        status: aiAvailable ? 'healthy' : 'warning',
        latency: aiAvailable ? 'full mode' : 'fallback mode',
        uptime: aiAvailable ? 'active' : 'degraded',
        icon: Cpu,
        port: null,
      },
      {
        name: 'Asset Registry (SQLite)',
        status: backendHealthy ? 'healthy' : 'warning',
        latency: `${systemStats.ready_assets} ready`,
        uptime: backendHealthy ? 'connected' : 'reconnect needed',
        icon: HardDrive,
        port: null,
      },
      {
        name: 'Violation Pipeline',
        status: systemStats.open_violations > 0 ? 'warning' : 'healthy',
        latency: `${systemStats.open_violations} open`,
        uptime: `${systemStats.high_severity_violations} high severity`,
        icon: Activity,
        port: null,
      },
      {
        name: 'Enforcement Engine',
        status: backendHealthy ? 'healthy' : 'warning',
        latency: `${systemStats.requests_last_minute}/min`,
        uptime: 'tracking',
        icon: Zap,
        port: null,
      },
      {
        name: 'Task Runner',
        status: taskMode === 'celery' ? 'healthy' : 'warning',
        latency: `${systemStats.queue_depth} queued`,
        uptime: taskMode === 'celery' ? 'distributed' : 'inline mode',
        icon: Wifi,
        port: null,
      },
      {
        name: 'Search Index',
        status: backendHealthy ? 'healthy' : 'warning',
        latency: `${systemStats.queued_assets} pending`,
        uptime: 'queryable',
        icon: Database,
        port: null,
      },
    ];
  }, [health, systemStats]);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">System Health</h1>
        <p className="page-subtitle">
          Live backend health, AI mode, and pipeline activity
        </p>
      </div>

      {loading && (
        <div className="card" style={{ marginBottom: 'var(--space-md)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Loading health telemetry...
        </div>
      )}

      {error && (
        <div className="card" style={{ marginBottom: 'var(--space-md)', fontSize: '0.85rem', color: 'var(--risk-critical)' }}>
          {error}
        </div>
      )}

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: 'var(--space-md)', marginBottom: 'var(--space-xl)',
      }}>
        {services.map((svc, idx) => {
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

      <div className="dashboard-grid-full">
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Cpu size={15} /> CPU Usage</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--risk-safe)', fontWeight: 600 }}>
              {cpuData[cpuData.length - 1]?.value || 0}%
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
              {memData[memData.length - 1]?.value || 0}%
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
              {queueData[queueData.length - 1]?.value || 0} tasks
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
              {latencyData[latencyData.length - 1]?.value || 0}ms
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
