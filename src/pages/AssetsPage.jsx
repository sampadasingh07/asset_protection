/* ═══════════════════════════════════════════════════════════════════════
   AssetsPage — Protected asset management + upload
   ═══════════════════════════════════════════════════════════════════════ */

import { useMemo, useState } from 'react';
import AssetUpload from '../components/AssetUpload';
import { generateAssets } from '../hooks/useMockData';
import {
  FileVideo, CheckCircle, Clock, Loader, Shield,
  MoreHorizontal, Fingerprint, Link
} from 'lucide-react';

const STATUS_CONFIG = {
  active: { label: 'Active', color: 'var(--risk-safe)', bg: 'var(--risk-safe-bg)', icon: CheckCircle },
  processing: { label: 'Processing', color: 'var(--risk-warning)', bg: 'var(--risk-warning-bg)', icon: Loader },
  fingerprinted: { label: 'Fingerprinted', color: 'var(--brand-primary-light)', bg: 'rgba(255, 255, 255,0.1)', icon: Fingerprint },
};

export default function AssetsPage() {
  const assets = useMemo(() => generateAssets(), []);
  const [showUpload, setShowUpload] = useState(false);

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Protected Assets</h1>
          <p className="page-subtitle">
            Manage fingerprinted media with blockchain-verified provenance
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(!showUpload)}>
          + Upload Asset
        </button>
      </div>

      {showUpload && (
        <div style={{ marginBottom: 'var(--space-xl)', animation: 'slideUp 0.3s ease' }}>
          <AssetUpload />
        </div>
      )}

      {/* Asset Cards Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
        gap: 'var(--space-md)',
      }}>
        {assets.map((asset, idx) => {
          const status = STATUS_CONFIG[asset.status] || STATUS_CONFIG.active;
          const StatusIcon = status.icon;

          return (
            <div
              key={asset.id}
              className="card animate-slide-up"
              style={{ animationDelay: `${idx * 60}ms`, cursor: 'pointer' }}
            >
              {/* Card Top */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-md)' }}>
                <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'center' }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 'var(--radius-sm)',
                    background: 'linear-gradient(135deg, var(--brand-primary), var(--brand-accent))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: 0.9,
                  }}>
                    <FileVideo size={20} color="white" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem', marginBottom: 2 }}>
                      {asset.name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {asset.filename}
                    </div>
                  </div>
                </div>
                <button style={{
                  background: 'none', border: 'none', color: 'var(--text-muted)',
                  cursor: 'pointer', padding: 4,
                }}>
                  <MoreHorizontal size={16} />
                </button>
              </div>

              {/* Status + Duration */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-md)',
                marginBottom: 'var(--space-md)',
              }}>
                <span style={{
                  display: 'inline-flex', alignItems: 'center', gap: '4px',
                  fontSize: '0.7rem', fontWeight: 600,
                  padding: '3px 10px', borderRadius: 'var(--radius-full)',
                  background: status.bg, color: status.color,
                }}>
                  <StatusIcon size={11} />
                  {status.label}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Clock size={11} /> {asset.duration}
                </span>
                {asset.blockchain_verified && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '3px',
                    fontSize: '0.65rem', fontWeight: 600,
                    color: 'var(--risk-safe)',
                  }}>
                    <Link size={10} /> On-chain
                  </span>
                )}
              </div>

              {/* Stats Row */}
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                padding: 'var(--space-md)',
                background: 'var(--bg-elevated)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
              }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem', marginBottom: 2 }}>Matches</div>
                  <div style={{ fontWeight: 600, color: asset.matches_count > 20 ? 'var(--risk-critical)' : 'var(--text-primary)' }}>
                    {asset.matches_count}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem', marginBottom: 2 }}>Avg Morph</div>
                  <div style={{
                    fontWeight: 600,
                    color: asset.morph_score_avg > 60 ? 'var(--risk-critical)' :
                           asset.morph_score_avg > 35 ? 'var(--risk-warning)' : 'var(--risk-safe)',
                  }}>
                    {asset.morph_score_avg}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem', marginBottom: 2 }}>Protection</div>
                  <div style={{ fontWeight: 600, color: 'var(--risk-safe)' }}>
                    <Shield size={12} style={{ marginRight: 2 }} />
                    Active
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

