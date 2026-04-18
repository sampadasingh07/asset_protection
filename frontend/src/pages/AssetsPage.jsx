/* ═══════════════════════════════════════════════════════════════════════
   AssetsPage — Protected asset management + upload
   ═══════════════════════════════════════════════════════════════════════ */

import { useCallback, useEffect, useState } from 'react';
import AssetUpload from '../components/AssetUpload';
import { fetchAssets, fetchViolations, searchAssetById, uploadAsset } from '../lib/api';
import {
  FileVideo, CheckCircle, Clock, Loader, Shield,
  MoreHorizontal, Fingerprint, Link
} from 'lucide-react';

const STATUS_CONFIG = {
  active: { label: 'Active', color: 'var(--risk-safe)', bg: 'var(--risk-safe-bg)', icon: CheckCircle },
  processing: { label: 'Processing', color: 'var(--risk-warning)', bg: 'var(--risk-warning-bg)', icon: Loader },
  fingerprinted: { label: 'Fingerprinted', color: 'var(--brand-primary-light)', bg: 'rgba(255, 255, 255,0.1)', icon: Fingerprint },
};

function mapAssetStatus(status) {
  if (status === 'queued' || status === 'processing') return 'processing';
  if (status === 'ready') return 'active';
  return 'active';
}

function formatDuration(contentType) {
  return contentType?.startsWith('video/') ? '--:--' : 'n/a';
}

function mapAsset(asset, violationStats) {
  const stats = violationStats.get(asset.id) || { matches_count: 0, morph_score_avg: 0 };
  return {
    id: asset.id,
    name: asset.title,
    filename: asset.file_name,
    filePath: asset.file_path,
    sourceUrl: asset.source_url,
    status: mapAssetStatus(asset.status),
    matches_count: stats.matches_count,
    morph_score_avg: stats.morph_score_avg,
    uploaded_at: asset.created_at,
    duration: formatDuration(asset.content_type),
    blockchain_verified: Array.isArray(asset.fingerprint_vector) && asset.fingerprint_vector.length > 0,
  };
}

function buildViolationStats(violations) {
  const grouped = new Map();

  for (const violation of violations) {
    const existing = grouped.get(violation.asset_id) || { count: 0, sum: 0 };
    existing.count += 1;
    existing.sum += Number(violation.confidence || 0) * 100;
    grouped.set(violation.asset_id, existing);
  }

  const normalized = new Map();
  for (const [assetId, value] of grouped.entries()) {
    normalized.set(assetId, {
      matches_count: value.count,
      morph_score_avg: value.count ? Math.round(value.sum / value.count) : 0,
    });
  }

  return normalized;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openMenuAssetId, setOpenMenuAssetId] = useState(null);

  const loadAssets = useCallback(async () => {
    setError('');
    setLoading(true);
    try {
      const [assetPayload, violations] = await Promise.all([
        fetchAssets(),
        fetchViolations(),
      ]);
      const violationStats = buildViolationStats(violations);
      setAssets(assetPayload.map((asset) => mapAsset(asset, violationStats)));
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Failed to load assets.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAssetAction = useCallback(async (action, asset) => {
    try {
      if (action === 'copy-path') {
        if (asset.filePath && navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(asset.filePath);
        }
      }

      if (action === 'open-source') {
        if (asset.sourceUrl) {
          window.open(asset.sourceUrl, '_blank', 'noopener,noreferrer');
        }
      }

      if (action === 'scan-similar') {
        const result = await searchAssetById(asset.id, 5);
        const count = Array.isArray(result) ? result.length : 0;
        window.alert(`Similarity scan found ${count} related result${count === 1 ? '' : 's'}.`);
      }
    } catch (actionError) {
      window.alert(actionError instanceof Error ? actionError.message : 'Asset action failed.');
    } finally {
      setOpenMenuAssetId(null);
    }
  }, []);

  const handleUpload = useCallback(async (file) => {
    const createdAsset = await uploadAsset(file);
    await loadAssets();
    return createdAsset;
  }, [loadAssets]);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

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
          <AssetUpload onUpload={handleUpload} />
        </div>
      )}

      {loading && (
        <div className="card" style={{ marginBottom: 'var(--space-md)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Loading assets...
        </div>
      )}

      {error && (
        <div className="card" style={{ marginBottom: 'var(--space-md)', color: 'var(--risk-critical)', fontSize: '0.85rem' }}>
          {error}
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
                }} onClick={() => setOpenMenuAssetId((current) => current === asset.id ? null : asset.id)}>
                  <MoreHorizontal size={16} />
                </button>
              </div>

              {openMenuAssetId === asset.id && (
                <div style={{
                  marginBottom: 'var(--space-md)',
                  padding: '6px',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-elevated)',
                  display: 'grid',
                  gap: '4px',
                }}>
                  <button className="btn btn-secondary" style={{ fontSize: '0.75rem' }} onClick={() => handleAssetAction('scan-similar', asset)}>
                    Scan Similar
                  </button>
                  <button className="btn btn-secondary" style={{ fontSize: '0.75rem' }} onClick={() => handleAssetAction('copy-path', asset)}>
                    Copy File Path
                  </button>
                  <button className="btn btn-secondary" style={{ fontSize: '0.75rem' }} onClick={() => handleAssetAction('open-source', asset)} disabled={!asset.sourceUrl}>
                    Open Source URL
                  </button>
                </div>
              )}

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
                    {asset.morph_score_avg}%
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

