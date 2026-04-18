/* ═══════════════════════════════════════════════════════════════════════
   EnforcementModal — Evidence bundle viewer with action controls
   ═══════════════════════════════════════════════════════════════════════ */

import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Shield, Gavel, Eye, XCircle, ExternalLink, Copy,
  CheckCircle, Link2, Fingerprint, Clock, AlertTriangle
} from 'lucide-react';

function getRiskLevel(score) {
  if (score > 70) return { label: 'HIGH RISK', color: '#FFFFFF', className: 'critical' };
  if (score > 40) return { label: 'MEDIUM', color: '#CCCCCC', className: 'warning' };
  return { label: 'LOW', color: '#888888', className: 'safe' };
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function EnforcementModal({ data, onClose, onAction }) {
  if (!data) return null;

  const risk = getRiskLevel(data.morph_score ?? 0);
  const flags = data.transformation_flags || {};
  const flagEntries = Object.entries(flags).filter(([, v]) => v);

  return (
    <AnimatePresence>
      <motion.div
        className="modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="modal-content"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="modal-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: 36, height: 36, borderRadius: 'var(--radius-sm)',
                background: risk.className === 'critical' ? 'var(--risk-critical-bg)' : 'var(--risk-warning-bg)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: risk.color,
              }}>
                <Shield size={18} />
              </div>
              <div>
                <div className="modal-title">Enforcement Action</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Violation #{data.violation_id?.slice(0, 8)}
                </div>
              </div>
            </div>
            <button className="modal-close" onClick={onClose}>
              <X size={16} />
            </button>
          </div>

          {/* Body */}
          <div className="modal-body">
            {/* Risk Assessment Banner */}
            <div style={{
              background: `linear-gradient(135deg, ${risk.color}11, transparent)`,
              border: `1px solid ${risk.color}33`,
              borderRadius: 'var(--radius-sm)',
              padding: 'var(--space-md) var(--space-lg)',
              marginBottom: 'var(--space-lg)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                  RISK ASSESSMENT
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 700, color: risk.color }}>
                    {data.morph_score}
                  </span>
                  <span className={`risk-badge ${risk.className}`}>{risk.label}</span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                  RECOMMENDED ACTION
                </div>
                <div style={{
                  fontSize: '0.9rem', fontWeight: 600,
                  color: data.morph_score > 80 ? 'var(--risk-critical)' : 'var(--risk-warning)',
                }}>
                  {data.morph_score > 80 ? '⚡ AUTO-TAKEDOWN' : '👁 HUMAN REVIEW'}
                </div>
              </div>
            </div>

            {/* Evidence Grid */}
            <div className="evidence-section">
              <div className="evidence-title">Match Evidence</div>
              <div className="evidence-grid">
                <div className="evidence-item">
                  <div className="evidence-item-label">Cosine Similarity</div>
                  <div className="evidence-item-value" style={{
                    color: data.cosine_similarity > 0.92 ? 'var(--risk-critical)' : 'var(--text-primary)',
                  }}>
                    {((data.cosine_similarity ?? 0) * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">GAN Score</div>
                  <div className="evidence-item-value">{data.gan_score ?? 0}/100</div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">DCT Frequency</div>
                  <div className="evidence-item-value">{data.freq_score ?? 0}/100</div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">Temporal Score</div>
                  <div className="evidence-item-value">{data.temporal_score ?? 0}/100</div>
                </div>
              </div>
            </div>

            {/* Infringement Details */}
            <div className="evidence-section">
              <div className="evidence-title">Infringement Details</div>
              <div className="evidence-grid">
                <div className="evidence-item">
                  <div className="evidence-item-label">Protected Asset</div>
                  <div className="evidence-item-value" style={{ fontSize: '0.825rem' }}>
                    {data.asset_name}
                  </div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">Platform</div>
                  <div className="evidence-item-value">
                    <span className={`platform-badge ${data.platform}`}>
                      {data.platform}
                    </span>
                  </div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">Offending Account</div>
                  <div className="evidence-item-value" style={{ color: 'var(--risk-critical)' }}>
                    {data.account_id}
                  </div>
                </div>
                <div className="evidence-item">
                  <div className="evidence-item-label">Discovered</div>
                  <div className="evidence-item-value" style={{ fontSize: '0.8rem' }}>
                    <Clock size={12} style={{ opacity: 0.5, marginRight: 4 }} />
                    {formatDate(data.discovered_at || new Date().toISOString())}
                  </div>
                </div>
              </div>
            </div>

            {/* Infringing URL */}
            <div className="evidence-section">
              <div className="evidence-title">Infringing URL</div>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)', padding: 'var(--space-md)',
                display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
                fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-secondary)',
              }}>
                <Link2 size={14} style={{ flexShrink: 0, opacity: 0.5 }} />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {data.infringing_url}
                </span>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => navigator.clipboard?.writeText(data.infringing_url)}
                  title="Copy URL"
                >
                  <Copy size={12} />
                </button>
              </div>
            </div>

            {/* Transformation Flags */}
            {flagEntries.length > 0 && (
              <div className="evidence-section">
                <div className="evidence-title">Detected Transformations</div>
                <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
                  {flagEntries.map(([key]) => (
                    <span key={key} className="risk-badge warning" style={{ fontSize: '0.7rem' }}>
                      <AlertTriangle size={10} />
                      {key.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Blockchain Proof */}
            <div className="evidence-section">
              <div className="evidence-title">Blockchain Provenance</div>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)', padding: 'var(--space-md)',
                display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
              }}>
                <Fingerprint size={16} style={{ color: 'var(--risk-safe)', flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 2 }}>
                    Ownership TX Hash (verified)
                  </div>
                  <div style={{
                    fontFamily: 'monospace', fontSize: '0.7rem',
                    color: 'var(--text-secondary)', wordBreak: 'break-all',
                  }}>
                    {data.blockchain_tx || 'n/a'}
                  </div>
                </div>
                <CheckCircle size={16} style={{ color: 'var(--risk-safe)', flexShrink: 0, marginLeft: 'auto' }} />
              </div>
            </div>

            {/* Propagation Info */}
            <div className="evidence-grid" style={{ marginBottom: 0 }}>
              <div className="evidence-item">
                <div className="evidence-item-label">Propagation Depth</div>
                <div className="evidence-item-value">{data.propagation_depth ?? 0} hops</div>
              </div>
              <div className="evidence-item">
                <div className="evidence-item-label">Estimated Views</div>
                <div className="evidence-item-value">{data.views_estimate?.toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={onClose}>
              <XCircle size={15} />
              Ignore
            </button>
            <button className="btn btn-primary" onClick={() => onAction?.('review', data)}>
              <Eye size={15} />
              Send to Review
            </button>
            <button className="btn btn-danger" onClick={() => onAction?.('takedown', data)}>
              <Gavel size={15} />
              File DMCA Takedown
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

